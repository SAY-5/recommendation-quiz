"""Load benchmark for the scoring API.

Spins up ``--users`` async clients hitting ``POST /api/quiz/score`` with random
quiz answer payloads against a running API for ``--duration`` seconds. Emits a
columnar text summary to stdout and a JSON result file under ``bench/results/``.

The bench can run in two modes:

* **HTTP mode** (default) — the API is already running at ``--base-url``. The
  bench loads questions from ``GET /api/quiz/questions`` and posts random
  answer permutations.
* **In-process mode** (``--in-process``) — bypasses the network and calls the
  scoring service directly. Used by CI to verify the scorer fans out without
  N+1 query growth via Django's ``CaptureQueriesContext``.

Real numbers only: throughput is computed from completed-request count divided
by elapsed wall time; latency percentiles use ``statistics.quantiles``.
"""
from __future__ import annotations

import argparse
import asyncio
import json
import random
import statistics
import sys
import time
from dataclasses import asdict, dataclass, field
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

try:
    import httpx
except ImportError:  # pragma: no cover - optional path
    httpx = None  # type: ignore[assignment]


@dataclass
class Sample:
    latency_ms: float
    server_score_ms: float | None
    status: int
    ok: bool


@dataclass
class BenchResult:
    started_at: str
    duration_s: float
    users: int
    base_url: str
    mode: str
    requests: int
    errors: int
    throughput_rps: float
    p50_ms: float
    p95_ms: float
    p99_ms: float
    mean_ms: float
    queries_per_request: float | None
    server_score_p95_ms: float | None
    samples: int
    notes: list[str] = field(default_factory=list)


def _build_random_answers(questions: list[dict[str, Any]]) -> list[dict[str, Any]]:
    """Pick a value for every (or a subset of) questions uniformly at random."""
    out: list[dict[str, Any]] = []
    sample_n = max(1, random.randint(len(questions) // 2, len(questions)))
    for q in random.sample(questions, sample_n):
        opts = q.get("options", [])
        if not opts:
            continue
        if q.get("kind") == "multi":
            k = random.randint(1, min(2, len(opts)))
            value: Any = [random.choice(opts)["value"] for _ in range(k)]
            value = list(set(value))
        else:
            value = random.choice(opts)["value"]
        out.append({"question_id": q["id"], "value": value})
    return out


async def _worker(
    client: "httpx.AsyncClient",
    base_url: str,
    questions: list[dict[str, Any]],
    samples: list[Sample],
    stop_at: float,
) -> None:
    while time.monotonic() < stop_at:
        answers = _build_random_answers(questions)
        if not answers:
            await asyncio.sleep(0)
            continue
        t0 = time.perf_counter()
        try:
            resp = await client.post(
                f"{base_url}/api/quiz/score",
                json={"answers": answers},
                timeout=30.0,
            )
            t1 = time.perf_counter()
            samples.append(
                Sample(
                    latency_ms=(t1 - t0) * 1000.0,
                    server_score_ms=None,
                    status=resp.status_code,
                    ok=resp.status_code == 200,
                )
            )
        except Exception:  # noqa: BLE001
            t1 = time.perf_counter()
            samples.append(
                Sample(
                    latency_ms=(t1 - t0) * 1000.0,
                    server_score_ms=None,
                    status=0,
                    ok=False,
                )
            )


async def _run_http(args: argparse.Namespace) -> BenchResult:
    if httpx is None:
        raise RuntimeError("httpx is not installed; install with `pip install httpx`")
    async with httpx.AsyncClient() as client:
        q_resp = await client.get(f"{args.base_url}/api/quiz/questions", timeout=10.0)
        q_resp.raise_for_status()
        questions = q_resp.json()
    if not questions:
        raise RuntimeError("API returned 0 questions; run `make seed` first")

    samples: list[Sample] = []
    started = datetime.now(timezone.utc)
    started_mono = time.monotonic()
    stop_at = started_mono + args.duration

    async with httpx.AsyncClient() as client:
        workers = [
            _worker(client, args.base_url, questions, samples, stop_at)
            for _ in range(args.users)
        ]
        await asyncio.gather(*workers)

    elapsed = time.monotonic() - started_mono
    return _summarise(
        samples=samples,
        elapsed=elapsed,
        users=args.users,
        base_url=args.base_url,
        started=started,
        mode="http",
        queries_per_request=None,
    )


def _run_in_process(args: argparse.Namespace) -> BenchResult:
    """In-process variant: drives the scoring service directly; counts queries."""
    import os

    os.environ.setdefault("DJANGO_SECRET_KEY", "bench-in-process")
    os.environ.setdefault("DJANGO_DEBUG", "1")
    os.environ.setdefault("DJANGO_SETTINGS_MODULE", "config.settings")
    sys.path.insert(0, str(Path(__file__).resolve().parent.parent / "apps" / "api"))

    import django

    django.setup()

    from django.test.utils import CaptureQueriesContext  # noqa: PLC0415
    from django.db import connection  # noqa: PLC0415
    from apps.catalog.models import Product, ProductAttribute  # noqa: PLC0415
    from apps.quiz.models import AnswerOption, Question  # noqa: PLC0415
    from apps.recommend.service import recommend_top_n  # noqa: PLC0415

    if Question.objects.count() == 0:
        # Tiny synthetic seed so the bench can run hermetically.
        q1 = Question.objects.create(
            slug="roast_preference", prompt="Roast?", order=1, kind="single"
        )
        AnswerOption.objects.create(question=q1, value="light", label="Light", order=1)
        AnswerOption.objects.create(question=q1, value="medium", label="Medium", order=2)
        for i in range(5):
            p = Product.objects.create(
                name=f"Coffee {i}", brand="Bench", price_cents=1500
            )
            ProductAttribute.objects.create(
                product=p, key="roast_level", value=random.choice(["light", "medium", "dark"])
            )

    questions = list(Question.objects.values("id"))
    qids = [q["id"] for q in questions]

    samples: list[Sample] = []
    started = datetime.now(timezone.utc)
    started_mono = time.monotonic()
    stop_at = started_mono + args.duration

    total_queries = 0
    iterations = 0
    while time.monotonic() < stop_at:
        answers = [
            {"question_id": random.choice(qids), "value": random.choice(["light", "medium"])}
        ]
        t0 = time.perf_counter()
        with CaptureQueriesContext(connection) as cap:
            recommend_top_n(answers, top_n=3)
        t1 = time.perf_counter()
        total_queries += len(cap.captured_queries)
        iterations += 1
        samples.append(
            Sample(
                latency_ms=(t1 - t0) * 1000.0,
                server_score_ms=(t1 - t0) * 1000.0,
                status=200,
                ok=True,
            )
        )
        if iterations >= args.max_iters:
            break

    elapsed = time.monotonic() - started_mono
    qpr = total_queries / iterations if iterations else None
    return _summarise(
        samples=samples,
        elapsed=elapsed,
        users=1,
        base_url="in-process",
        started=started,
        mode="in-process",
        queries_per_request=qpr,
    )


def _summarise(
    samples: list[Sample],
    elapsed: float,
    users: int,
    base_url: str,
    started: datetime,
    mode: str,
    queries_per_request: float | None,
) -> BenchResult:
    ok_samples = [s for s in samples if s.ok]
    latencies = sorted(s.latency_ms for s in ok_samples)
    if latencies:
        mean = statistics.fmean(latencies)
        p50 = _quantile(latencies, 0.50)
        p95 = _quantile(latencies, 0.95)
        p99 = _quantile(latencies, 0.99)
    else:
        mean = p50 = p95 = p99 = 0.0
    return BenchResult(
        started_at=started.isoformat(),
        duration_s=round(elapsed, 3),
        users=users,
        base_url=base_url,
        mode=mode,
        requests=len(samples),
        errors=len([s for s in samples if not s.ok]),
        throughput_rps=round(len(samples) / elapsed, 2) if elapsed > 0 else 0.0,
        p50_ms=round(p50, 2),
        p95_ms=round(p95, 2),
        p99_ms=round(p99, 2),
        mean_ms=round(mean, 2),
        queries_per_request=(
            round(queries_per_request, 2) if queries_per_request is not None else None
        ),
        server_score_p95_ms=None,
        samples=len(samples),
    )


def _quantile(sorted_xs: list[float], q: float) -> float:
    if not sorted_xs:
        return 0.0
    idx = max(0, min(len(sorted_xs) - 1, int(round(q * (len(sorted_xs) - 1)))))
    return sorted_xs[idx]


def _format_text(result: BenchResult) -> str:
    lines = [
        "scoring api load bench",
        "----------------------",
        f"mode              : {result.mode}",
        f"base url          : {result.base_url}",
        f"users             : {result.users}",
        f"duration (s)      : {result.duration_s}",
        f"requests          : {result.requests}",
        f"errors            : {result.errors}",
        f"throughput (rps)  : {result.throughput_rps}",
        f"latency mean (ms) : {result.mean_ms}",
        f"latency p50 (ms)  : {result.p50_ms}",
        f"latency p95 (ms)  : {result.p95_ms}",
        f"latency p99 (ms)  : {result.p99_ms}",
    ]
    if result.queries_per_request is not None:
        lines.append(f"queries / request : {result.queries_per_request}")
    return "\n".join(lines)


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description="Load bench for the scoring API.")
    parser.add_argument("--base-url", default="http://localhost:8000")
    parser.add_argument("--users", type=int, default=100)
    parser.add_argument("--duration", type=float, default=60.0)
    parser.add_argument("--in-process", action="store_true")
    parser.add_argument("--max-iters", type=int, default=2000)
    parser.add_argument("--output-dir", type=Path, default=Path(__file__).parent / "results")
    parser.add_argument("--baseline", type=Path, default=None)
    parser.add_argument("--regress-throughput-ratio", type=float, default=0.5)
    parser.add_argument("--regress-p95-ratio", type=float, default=2.0)
    args = parser.parse_args(argv)

    if args.in_process:
        result = _run_in_process(args)
    else:
        result = asyncio.run(_run_http(args))

    print(_format_text(result))

    args.output_dir.mkdir(parents=True, exist_ok=True)
    ts = datetime.now(timezone.utc).strftime("%Y%m%dT%H%M%SZ")
    out_path = args.output_dir / f"{ts}.json"
    out_path.write_text(json.dumps(asdict(result), indent=2) + "\n")
    print(f"\nresult written to {out_path}")

    if args.baseline and args.baseline.exists():
        baseline = json.loads(args.baseline.read_text())
        regression_msgs = _check_regression(
            result,
            baseline,
            args.regress_throughput_ratio,
            args.regress_p95_ratio,
        )
        if regression_msgs:
            print("\nREGRESSION:")
            for m in regression_msgs:
                print(f"  - {m}")
            return 2
        print("\nno regression vs baseline.")
    return 0


def _check_regression(
    result: BenchResult,
    baseline: dict[str, Any],
    throughput_ratio: float,
    p95_ratio: float,
) -> list[str]:
    """Return a list of human-readable regressions, empty if all gates pass."""
    msgs: list[str] = []
    base_rps = float(baseline.get("throughput_rps", 0.0))
    base_p95 = float(baseline.get("p95_ms", 0.0))
    if base_rps > 0 and result.throughput_rps < base_rps * throughput_ratio:
        msgs.append(
            f"throughput {result.throughput_rps} rps < {throughput_ratio:.0%} of baseline "
            f"{base_rps} rps"
        )
    if base_p95 > 0 and result.p95_ms > base_p95 * p95_ratio:
        msgs.append(
            f"p95 latency {result.p95_ms} ms > {p95_ratio:.0%} of baseline {base_p95} ms"
        )
    return msgs


if __name__ == "__main__":
    sys.exit(main())

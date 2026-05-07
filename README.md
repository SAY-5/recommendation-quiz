# recommendation-quiz

A multi-step product recommendation quiz. Users answer twelve questions about
their coffee preferences (roast, brew method, caffeine, budget, ...), the
backend scores their answers against a catalog of 30 products using a
weighted-attribute algorithm, and the frontend displays the top three matches
with a per-product reason summary.

The quiz uses coffee as a worked example domain. The scoring engine itself is
domain-agnostic — swap the seed data and the question/attribute mapping and
it scores anything you can express as a set of attributes.

## Tech stack

| Layer | Choice |
|---|---|
| Frontend | React 18, TypeScript, Vite, Tailwind CSS, React Router |
| Backend | Python 3.12, Django 5, DRF, drf-spectacular |
| Database | PostgreSQL 16 |
| Tests | pytest + factory_boy (api), Vitest + Testing Library (web), Playwright (e2e) |
| Lint / types | ruff + mypy strict (api), eslint + prettier + tsc (web) |
| Container | Multi-stage Dockerfile per service, docker-compose for local dev |
| Deploy target | Documented Terraform stub for ECS Fargate + RDS + S3/CloudFront (not provisioned) |

## Quickstart

Prerequisites: Docker, Node 20, pnpm 10, Python 3.12, Poetry 2.

```bash
# Bring up Postgres
docker compose up -d postgres

# Backend
cd apps/api
poetry install
poetry run python manage.py migrate
poetry run python manage.py seed_catalog
poetry run python manage.py runserver

# Frontend (in a second shell)
cd apps/web
pnpm install
pnpm dev
```

Open `http://localhost:5173`.

The OpenAPI 3.1 schema is served at `http://localhost:8000/api/schema/`, with
Swagger UI at `http://localhost:8000/api/docs/`.

## Endpoints

| Method | Path | Description |
|---|---|---|
| `GET` | `/api/quiz/questions` | Full ordered list of questions and options. |
| `POST` | `/api/quiz/score` | Score an answer set, return top-3 products with reasons. |
| `GET` | `/api/products/{id}` | Product detail with all attributes. |

Errors use a consistent envelope: `{ code, message, retryable, request_id }`.

## Testing

```bash
make test       # pytest + vitest
make lint       # ruff + eslint + prettier
make typecheck  # mypy + tsc
make e2e        # Playwright cross-browser
```

Backend coverage gate: 85% (currently ~95%). Each pytest run prints the table.
Frontend coverage gate: 75% over `src/components` and `src/lib`; pages are
exercised end-to-end via Playwright.

The backend test suite includes Hypothesis property tests
(`tests/test_scoring_properties.py`) that assert score-bound, subset-
monotonicity, and hard-incompatibility invariants over randomly generated
answer-and-product combinations.

End-to-end suite stubs the API at the network layer (Playwright `route`
handlers), so it runs hermetically — no live backend required.

## Bench

```bash
make bench           # 30s in-process load against the scoring service
make bench-regress   # bench + compare to bench/baselines/baseline-in-process.json
```

The bench writes a JSON record to `bench/results/` per run. Reference numbers
from a 20s in-process run on a 2024 M-series laptop, sqlite-backed:

| metric              | value      |
| ------------------- | ---------- |
| throughput          | 302.71 rps |
| latency mean        | 3.25 ms    |
| latency p50         | 2.95 ms    |
| latency p95         | 5.27 ms    |
| latency p99         | 6.43 ms    |
| queries per request | 1.8        |

Queries-per-request below ~4 confirms the scorer pulls products in a single
prefetched query (`Product.objects.prefetch_related("attributes")`) rather
than per-product. The bench uses Django's `CaptureQueriesContext` to count
queries on each ``recommend_top_n`` call. Baseline lives at
``bench/baselines/baseline-in-process.json``; the CI ``bench-api`` job runs a
30 s scaled-down bench and fails on ≥ 50 % throughput drop or ≥ 2× p95 growth.

`bench/load.py --in-process` drives the scoring service directly and counts
queries; `bench/load.py` (default) hits a running API at ``--base-url`` with
``--users`` async clients via ``httpx`` and is what you'd run against a
deployed environment.

## Mobile performance

The frontend is mobile-first: a single visual card per quiz step, lazy-loaded
product images with `srcset`, code-split routes (each page is its own chunk),
and inline critical CSS in `index.html` for first paint.

Lighthouse numbers from a real run: `<TBD: run lighthouse locally and paste
the four scores here>`. The `lighthouse.yml` workflow runs an audit on the
built bundle weekly and uploads the JSON report as an artifact, but its
output is informational only — Lighthouse perf scores are not deterministic
on shared CI runners and do not gate merges.

## What this is not

* No user accounts, sessions, or auth — the quiz is anonymous and the only
  per-user state is `localStorage` on the client.
* No purchase, checkout, payments, or inventory tracking. Products are
  reference data; clicking a result does nothing beyond showing the card.
* No machine-learned recommendations engine. Scoring is deterministic and
  rules-based; see `apps/api/apps/recommend/scoring.py`.
* No live AWS deployment. `infra/aws/` is a documented Terraform stub, not
  applied or validated against an account.
* No image CDN. `image_url` on the product model is currently empty in the
  seed data; the UI falls back to a numbered badge.

## Project layout

```
apps/
  api/          Django + DRF backend (quiz, catalog, recommend apps)
  web/          React + Vite frontend
infra/aws/      Terraform stub for the AWS deploy target
scripts/        Helper scripts (seed wrapper)
.github/        CI workflows
```

See [`ARCHITECTURE.md`](./ARCHITECTURE.md) for the data model, scoring
walkthrough, and deploy-target reference.

## License

MIT — see [`LICENSE`](./LICENSE).

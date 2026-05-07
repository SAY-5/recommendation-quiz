import { useEffect, useState } from "react";
import type { QuestionContribution, Recommendation } from "../lib/api";
import { formatPrice } from "../lib/format";

interface ProductCardProps {
  recommendation: Recommendation;
  rank: number;
}

const MOBILE_BREAKPOINT_PX = 640;

export function ProductCard({ recommendation, rank }: ProductCardProps) {
  const { product, score, reasons, breakdown = [] } = recommendation;
  const [open, setOpen] = useState<boolean>(() => !isMobileViewport());

  useEffect(() => {
    function onResize() {
      // Only flip closed when crossing into mobile; never auto-close after a
      // user explicitly opened the section on a desktop tab.
      if (isMobileViewport()) setOpen(false);
    }
    window.addEventListener("resize", onResize);
    return () => window.removeEventListener("resize", onResize);
  }, []);

  return (
    <article className="overflow-hidden rounded-2xl bg-white shadow-sm ring-1 ring-bean-100">
      <div className="flex flex-col gap-4 p-5 sm:flex-row sm:p-6">
        {product.image_url ? (
          <img
            src={product.image_url}
            alt=""
            loading="lazy"
            decoding="async"
            srcSet={buildSrcSet(product.image_url)}
            sizes="(min-width: 640px) 160px, 33vw"
            width={160}
            height={160}
            className="h-40 w-full rounded-xl object-cover sm:h-40 sm:w-40"
          />
        ) : (
          <div
            aria-hidden="true"
            className="flex h-40 w-full shrink-0 items-center justify-center rounded-xl bg-bean-100 text-3xl font-semibold text-bean-700 sm:w-40"
          >
            #{rank}
          </div>
        )}
        <div className="flex-1">
          <p className="text-xs uppercase tracking-wider text-bean-500">{product.brand}</p>
          <h2 className="mt-1 text-lg font-semibold sm:text-xl">{product.name}</h2>
          <p className="mt-1 text-sm text-bean-700">{formatPrice(product.price_cents)}</p>
          <p className="mt-3 text-xs text-bean-500">
            Match score: <span className="font-mono">{score.toFixed(2)}</span>
          </p>
          {reasons.length > 0 && (
            <ul className="mt-3 space-y-1 text-sm text-bean-900">
              {reasons.map((reason) => (
                <li key={reason} className="flex gap-2">
                  <span aria-hidden="true" className="text-bean-500">
                    •
                  </span>
                  <span>{reason}</span>
                </li>
              ))}
            </ul>
          )}
          {breakdown.length > 0 && (
            <div className="mt-4 border-t border-bean-100 pt-3">
              <button
                type="button"
                aria-expanded={open}
                aria-controls={`breakdown-${product.id}`}
                onClick={() => setOpen((v) => !v)}
                className="text-xs font-semibold uppercase tracking-wider text-bean-700 hover:text-bean-900"
              >
                {open ? "Hide" : "Show"} why this match? ({breakdown.length})
              </button>
              {open && (
                <ul id={`breakdown-${product.id}`} className="mt-3 space-y-2">
                  {breakdown.map((c) => (
                    <BreakdownRow key={c.question_id} contribution={c} />
                  ))}
                </ul>
              )}
            </div>
          )}
        </div>
      </div>
    </article>
  );
}

function BreakdownRow({ contribution: c }: { contribution: QuestionContribution }) {
  const ratio =
    c.max_contribution_pts > 0
      ? Math.max(0, Math.min(1, c.contribution_pts / c.max_contribution_pts))
      : 0;
  const widthPct = `${(ratio * 100).toFixed(0)}%`;
  const userAnswerLabel = renderAnswer(c.user_answer);
  return (
    <li
      data-testid={`breakdown-row-${c.question_id}`}
      className="rounded-lg bg-bean-50 px-3 py-2 text-xs"
    >
      <div className="flex items-center justify-between gap-3">
        <p className="font-medium text-bean-900">{c.question_prompt}</p>
        <span className="font-mono text-bean-700">
          {c.contribution_pts.toFixed(1)} / {c.max_contribution_pts.toFixed(1)}
        </span>
      </div>
      <div
        role="progressbar"
        aria-valuemin={0}
        aria-valuemax={c.max_contribution_pts}
        aria-valuenow={c.contribution_pts}
        aria-label={c.question_prompt}
        className="mt-1 h-2 w-full rounded-full bg-bean-100"
      >
        <div
          className="h-full rounded-full bg-bean-700 transition-all"
          style={{ width: widthPct }}
        />
      </div>
      <p className="mt-1 text-bean-700">
        Your answer: <span className="font-medium text-bean-900">{userAnswerLabel}</span> —{" "}
        <span>{c.why}</span>
      </p>
    </li>
  );
}

function renderAnswer(value: QuestionContribution["user_answer"]): string {
  if (value === null || value === undefined) return "—";
  if (Array.isArray(value)) return value.join(", ");
  return String(value);
}

function isMobileViewport(): boolean {
  if (typeof window === "undefined") return false;
  return window.innerWidth < MOBILE_BREAKPOINT_PX;
}

function buildSrcSet(url: string): string | undefined {
  if (!url || url.startsWith("data:")) return undefined;
  return `${url} 1x, ${url} 2x`;
}

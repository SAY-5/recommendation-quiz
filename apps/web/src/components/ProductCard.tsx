import type { Recommendation } from "../lib/api";
import { formatPrice } from "../lib/format";

interface ProductCardProps {
  recommendation: Recommendation;
  rank: number;
}

export function ProductCard({ recommendation, rank }: ProductCardProps) {
  const { product, score, reasons } = recommendation;
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
        </div>
      </div>
    </article>
  );
}

function buildSrcSet(url: string): string | undefined {
  if (!url || url.startsWith("data:")) return undefined;
  return `${url} 1x, ${url} 2x`;
}

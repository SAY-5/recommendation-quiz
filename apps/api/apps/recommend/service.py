"""Boundary layer between the ORM and the pure scoring functions."""
from __future__ import annotations

from typing import Any

from apps.catalog.models import Product
from apps.quiz.models import Question

from .scoring import score_products


def _load_products() -> list[dict[str, Any]]:
    products = Product.objects.prefetch_related("attributes").all()
    payload: list[dict[str, Any]] = []
    for p in products:
        attrs: dict[str, Any] = {a.key: a.value for a in p.attributes.all()}
        payload.append({"id": p.id, "attributes": attrs})
    return payload


def _load_question_slug_map(question_ids: list[int]) -> dict[int, str]:
    rows = Question.objects.filter(id__in=question_ids).values_list("id", "slug")
    return {int(qid): slug for qid, slug in rows}


def recommend_top_n(answers: list[dict[str, Any]], top_n: int = 3) -> list[dict[str, Any]]:
    """Return the top-N products with their score and reasons."""
    if not answers:
        return []

    question_ids = [int(a["question_id"]) for a in answers]
    slug_map = _load_question_slug_map(question_ids)
    products = _load_products()

    scored = score_products(answers, products, slug_map)
    top = [s for s in scored if s.score > 0][:top_n]
    if not top:
        return []

    product_index = {p.id: p for p in Product.objects.filter(id__in=[s.product_id for s in top])}
    out: list[dict[str, Any]] = []
    for s in top:
        product = product_index.get(s.product_id)
        if product is None:
            continue
        out.append(
            {
                "product": {
                    "id": product.id,
                    "name": product.name,
                    "brand": product.brand,
                    "price_cents": product.price_cents,
                    "image_url": product.image_url,
                },
                "score": s.score,
                "reasons": s.reasons,
            }
        )
    return out

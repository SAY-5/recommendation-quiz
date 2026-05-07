"""Boundary layer between the ORM and the pure scoring functions."""
from __future__ import annotations

from typing import Any

from apps.catalog.models import Product
from apps.quiz.models import Question

from .models import QuizSubmission, ScoringVariant
from .scoring import VariantConfig, score_products


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


def _resolve_variant(name: str | None) -> ScoringVariant | None:
    """Return an active variant by name. ``None``/unknown → ``None`` (default)."""
    if not name:
        return ScoringVariant.objects.filter(name="default", is_active=True).first()
    return ScoringVariant.objects.filter(name=name, is_active=True).first()


def _to_variant_config(variant: ScoringVariant | None) -> VariantConfig:
    if variant is None:
        return VariantConfig()
    return VariantConfig(
        name=variant.name,
        weight_overrides=variant.weight_overrides(),
        hard_fail_slugs=tuple(variant.hard_fail_slugs()),
    )


def recommend_top_n(
    answers: list[dict[str, Any]],
    top_n: int = 3,
    variant_name: str | None = None,
    *,
    persist: bool = False,
    session_id: str = "",
) -> list[dict[str, Any]]:
    """Return the top-N products with their score and reasons.

    If ``persist=True`` and a variant resolves successfully, a
    ``QuizSubmission`` row is recorded with the resulting recommendations.
    """
    if not answers:
        return []

    question_ids = [int(a["question_id"]) for a in answers]
    slug_map = _load_question_slug_map(question_ids)
    products = _load_products()

    variant = _resolve_variant(variant_name)
    cfg = _to_variant_config(variant)
    scored = score_products(answers, products, slug_map, variant=cfg)
    top = [s for s in scored if s.score > 0][:top_n]
    if not top:
        if persist and variant is not None:
            QuizSubmission.objects.create(
                variant=variant,
                answers=answers,
                recommendations=[],
                session_id=session_id,
            )
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
    if persist and variant is not None:
        QuizSubmission.objects.create(
            variant=variant,
            answers=answers,
            recommendations=out,
            session_id=session_id,
        )
    return out

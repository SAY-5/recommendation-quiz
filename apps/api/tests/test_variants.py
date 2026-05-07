"""Tests for variant-aware scoring and submission persistence."""
from __future__ import annotations

import pytest

from apps.catalog.models import Product, ProductAttribute
from apps.quiz.models import AnswerOption, Question
from apps.recommend.models import QuizSubmission, ScoringVariant
from apps.recommend.scoring import VariantConfig, score_products
from apps.recommend.service import recommend_top_n

pytestmark = pytest.mark.django_db


def _seed_minimal() -> dict[str, int]:
    q_roast = Question.objects.create(
        slug="roast_preference", prompt="Roast?", order=1, kind="single"
    )
    AnswerOption.objects.create(question=q_roast, value="light", label="Light", order=1)
    q_flavor = Question.objects.create(
        slug="flavor_profile", prompt="Flavor?", order=2, kind="multi"
    )
    AnswerOption.objects.create(question=q_flavor, value="fruity", label="Fruity", order=1)
    q_budget = Question.objects.create(slug="budget", prompt="Budget?", order=3, kind="single")
    AnswerOption.objects.create(question=q_budget, value="budget", label="Budget", order=1)

    p_match = Product.objects.create(name="Match", brand="X", price_cents=1500)
    ProductAttribute.objects.create(product=p_match, key="roast_level", value="light")
    ProductAttribute.objects.create(
        product=p_match, key="flavor_profile", value=["fruity"]
    )
    ProductAttribute.objects.create(product=p_match, key="price_tier", value="budget")

    p_overpriced = Product.objects.create(name="Lux", brand="X", price_cents=4500)
    ProductAttribute.objects.create(product=p_overpriced, key="roast_level", value="light")
    ProductAttribute.objects.create(
        product=p_overpriced, key="flavor_profile", value=["fruity"]
    )
    ProductAttribute.objects.create(
        product=p_overpriced, key="price_tier", value="premium"
    )
    return {
        "q_roast": q_roast.id,
        "q_flavor": q_flavor.id,
        "q_budget": q_budget.id,
        "p_match": p_match.id,
        "p_overpriced": p_overpriced.id,
    }


def test_default_variant_falls_back_to_default_weights() -> None:
    """Calling the scorer with ``variant=None`` matches an explicit default config."""
    products = [
        {"id": 1, "attributes": {"roast_level": "light"}},
    ]
    answers = [{"question_id": 1, "value": "light"}]
    slug_map = {1: "roast_preference"}
    a = score_products(answers, products, slug_map)
    b = score_products(answers, products, slug_map, variant=VariantConfig())
    assert [(s.product_id, s.score) for s in a] == [(s.product_id, s.score) for s in b]


def test_flavor_heavy_variant_doubles_flavor_contribution() -> None:
    """The flavor_heavy override doubles the flavor_profile rule weight."""
    products = [
        {
            "id": 1,
            "attributes": {"flavor_profile": ["fruity"], "roast_level": "light"},
        },
    ]
    answers = [
        {"question_id": 1, "value": "fruity"},
        {"question_id": 2, "value": "light"},
    ]
    slug_map = {1: "flavor_profile", 2: "roast_preference"}
    default_score = score_products(answers, products, slug_map)[0].score
    boosted = score_products(
        answers,
        products,
        slug_map,
        variant=VariantConfig(name="flavor_heavy", weight_overrides={"flavor_profile": 2.0}),
    )[0].score
    # The flavor rule weight is 2.0; default contributes 2.0, boosted 4.0.
    assert boosted == default_score + 2.0


def test_budget_strict_variant_zeroes_overpriced_products() -> None:
    """``budget_strict`` flips a product's score to 0 when budget mismatches hard."""
    products = [
        {
            "id": 1,
            "attributes": {"price_tier": "premium", "roast_level": "light"},
        },
        {
            "id": 2,
            "attributes": {"price_tier": "budget", "roast_level": "light"},
        },
    ]
    answers = [
        {"question_id": 1, "value": "budget"},
        {"question_id": 2, "value": "light"},
    ]
    slug_map = {1: "budget", 2: "roast_preference"}
    strict = score_products(
        answers,
        products,
        slug_map,
        variant=VariantConfig(name="budget_strict", hard_fail_slugs=("budget",)),
    )
    by_id = {s.product_id: s for s in strict}
    # premium product gets full ordinal partial credit normally but the
    # variant collapses it to 0 because the budget slug match scored 0.0.
    assert by_id[1].score == 0.0
    # budget-tier product is unaffected.
    assert by_id[2].score > 0.0


def test_score_endpoint_persists_submission_when_variant_resolves(
    api_client,
) -> None:
    ScoringVariant.objects.create(
        name="default", description="default", weights={}, hard_fail_keys=[]
    )
    ids = _seed_minimal()
    response = api_client.post(
        "/api/quiz/score",
        data={
            "answers": [
                {"question_id": ids["q_roast"], "value": "light"},
                {"question_id": ids["q_flavor"], "value": "fruity"},
                {"question_id": ids["q_budget"], "value": "budget"},
            ]
        },
        format="json",
    )
    assert response.status_code == 200
    assert QuizSubmission.objects.count() == 1
    sub = QuizSubmission.objects.first()
    assert sub is not None
    assert sub.variant.name == "default"
    assert sub.recommendations  # truthy


def test_score_endpoint_routes_to_named_variant(api_client) -> None:
    ScoringVariant.objects.create(
        name="default", description="default", weights={}, hard_fail_keys=[]
    )
    ScoringVariant.objects.create(
        name="flavor_heavy",
        description="boost flavor",
        weights={"flavor_profile": 2.0},
        hard_fail_keys=[],
    )
    ids = _seed_minimal()
    payload = {
        "answers": [
            {"question_id": ids["q_roast"], "value": "light"},
            {"question_id": ids["q_flavor"], "value": "fruity"},
            {"question_id": ids["q_budget"], "value": "budget"},
        ]
    }
    api_client.post("/api/quiz/score?variant=flavor_heavy", data=payload, format="json")
    api_client.post("/api/quiz/score", data=payload, format="json")
    by_variant = {s.variant.name for s in QuizSubmission.objects.all()}
    assert by_variant == {"default", "flavor_heavy"}


def test_recommend_top_n_no_variant_named_default_uses_pure_defaults() -> None:
    """If no ScoringVariant rows exist, the scorer still works (no persistence)."""
    ids = _seed_minimal()
    out = recommend_top_n(
        [{"question_id": ids["q_roast"], "value": "light"}],
        top_n=3,
    )
    assert out  # produces recommendations
    assert QuizSubmission.objects.count() == 0  # no variant → no persist

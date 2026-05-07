"""Tests for the v4 explain-why breakdown payload."""
from __future__ import annotations

import pytest

from apps.catalog.models import Product, ProductAttribute
from apps.quiz.models import AnswerOption, Question
from apps.recommend.scoring import score_products
from apps.recommend.service import recommend_top_n

pytestmark = pytest.mark.django_db


def _seed() -> dict[str, int]:
    q_roast = Question.objects.create(
        slug="roast_preference", prompt="Roast?", order=1, kind="single"
    )
    AnswerOption.objects.create(question=q_roast, value="light", label="Light", order=1)
    q_flavor = Question.objects.create(
        slug="flavor_profile", prompt="Flavor?", order=2, kind="multi"
    )
    AnswerOption.objects.create(question=q_flavor, value="fruity", label="Fruity", order=1)
    q_brew = Question.objects.create(
        slug="brew_method", prompt="Brew?", order=3, kind="single"
    )
    AnswerOption.objects.create(question=q_brew, value="drip", label="Drip", order=1)

    p = Product.objects.create(name="P", brand="X", price_cents=1500)
    ProductAttribute.objects.create(product=p, key="roast_level", value="light")
    ProductAttribute.objects.create(product=p, key="flavor_profile", value=["fruity"])
    ProductAttribute.objects.create(
        product=p, key="brew_method_compatibility", value=["drip"]
    )
    return {
        "q_roast": q_roast.id,
        "q_flavor": q_flavor.id,
        "q_brew": q_brew.id,
        "p": p.id,
    }


def test_breakdown_sums_equals_total_score() -> None:
    """The sum of per-question contribution_pts equals the total product score."""
    products = [
        {
            "id": 1,
            "attributes": {
                "roast_level": "light",
                "flavor_profile": ["fruity", "floral"],
                "brew_method_compatibility": ["drip"],
                "price_tier": "budget",
            },
        }
    ]
    answers = [
        {"question_id": 1, "value": "light"},
        {"question_id": 2, "value": "fruity"},
        {"question_id": 3, "value": "drip"},
        {"question_id": 4, "value": "budget"},
    ]
    slug_map = {
        1: "roast_preference",
        2: "flavor_profile",
        3: "brew_method",
        4: "budget",
    }
    scored = score_products(answers, products, slug_map)[0]
    contribution_total = sum(c.contribution_pts for c in scored.breakdown)
    # Within float tolerance — both sides go through the same accumulation,
    # but the total is rounded after the loop and contributions are rounded
    # per-question, so we check approximate equality.
    assert abs(contribution_total - scored.score) < 1e-3


def test_breakdown_includes_zero_contributions() -> None:
    """Breakdown contains an entry for every answer, even if contribution is 0."""
    products = [
        {
            "id": 1,
            "attributes": {
                "roast_level": "dark",
                "flavor_profile": ["earthy"],
            },
        }
    ]
    answers = [
        {"question_id": 1, "value": "light"},  # mismatch
        {"question_id": 2, "value": "fruity"},  # mismatch
    ]
    slug_map = {1: "roast_preference", 2: "flavor_profile"}
    scored = score_products(answers, products, slug_map)[0]
    assert len(scored.breakdown) == 2
    # One mismatch is ordinal (gets 0.5 partial credit at distance 2 → 0).
    # Light vs dark: distance=2 → score 0.0
    roast_entry = next(c for c in scored.breakdown if c.question_slug == "roast_preference")
    assert roast_entry.contribution_pts == 0.0
    assert "no match" in roast_entry.why or "0.0" in roast_entry.why
    flavor_entry = next(c for c in scored.breakdown if c.question_slug == "flavor_profile")
    assert flavor_entry.contribution_pts == 0.0


def test_score_endpoint_returns_breakdown_field(api_client) -> None:
    ids = _seed()
    response = api_client.post(
        "/api/quiz/score",
        data={
            "answers": [
                {"question_id": ids["q_roast"], "value": "light"},
                {"question_id": ids["q_flavor"], "value": "fruity"},
                {"question_id": ids["q_brew"], "value": "drip"},
            ]
        },
        format="json",
    )
    assert response.status_code == 200
    rec = response.json()["recommendations"][0]
    assert "breakdown" in rec
    assert "reasons" in rec  # back-compat retained
    breakdown = rec["breakdown"]
    assert len(breakdown) == 3
    for entry in breakdown:
        assert set(entry.keys()) == {
            "question_id",
            "question_prompt",
            "user_answer",
            "contribution_pts",
            "max_contribution_pts",
            "why",
        }
    # Sum approximately equals score.
    total = sum(e["contribution_pts"] for e in breakdown)
    assert abs(total - rec["score"]) < 1e-3


def test_breakdown_includes_question_prompt_strings(api_client) -> None:
    ids = _seed()
    response = api_client.post(
        "/api/quiz/score",
        data={
            "answers": [
                {"question_id": ids["q_roast"], "value": "light"},
                {"question_id": ids["q_flavor"], "value": "fruity"},
            ]
        },
        format="json",
    )
    rec = response.json()["recommendations"][0]
    prompts = {e["question_prompt"] for e in rec["breakdown"]}
    assert prompts == {"Roast?", "Flavor?"}


def test_recommend_top_n_top_products_have_well_formed_breakdown() -> None:
    ids = _seed()
    out = recommend_top_n(
        [
            {"question_id": ids["q_roast"], "value": "light"},
        ],
        top_n=3,
    )
    assert out
    for rec in out:
        assert "breakdown" in rec
        for entry in rec["breakdown"]:
            assert entry["max_contribution_pts"] >= entry["contribution_pts"]

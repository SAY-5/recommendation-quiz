"""Decision-table tests for the pure scoring functions."""
from __future__ import annotations

import pytest

from apps.recommend.scoring import (
    ROAST_ORDER,
    AttributeRule,
    match_score,
    score_products,
)


@pytest.mark.parametrize(
    ("target", "value", "expected"),
    [
        ("medium", "medium", 1.0),
        ("medium", "light", 0.5),
        ("medium", "dark", 0.5),
        ("light", "dark", 0.0),
        ("light", "light", 1.0),
    ],
)
def test_ordinal_falloff(target: str, value: str, expected: float) -> None:
    rule = AttributeRule(
        attribute_key="roast_level",
        weight=1.0,
        kind="ordinal",
        ordinal_order=ROAST_ORDER,
    )
    assert match_score(rule, target, value) == pytest.approx(expected)


def test_exact_match() -> None:
    rule = AttributeRule(attribute_key="milk_friendly", weight=1.0, kind="exact")
    assert match_score(rule, True, True) == 1.0
    assert match_score(rule, True, False) == 0.0


def test_membership_overlap() -> None:
    rule = AttributeRule(attribute_key="flavor_profile", weight=1.0, kind="membership")
    assert match_score(rule, "fruity", ["fruity", "floral"]) == 1.0
    assert match_score(rule, ["nutty", "earthy"], ["fruity", "floral"]) == 0.0
    assert match_score(rule, ["nutty", "earthy"], ["earthy"]) == 1.0


def test_membership_hard_incompatibility() -> None:
    """Brew method mismatch returns zero (espresso-only product, drip user)."""
    rule = AttributeRule(attribute_key="brew_method_compatibility", weight=3.0, kind="membership")
    assert match_score(rule, "drip", ["espresso"]) == 0.0


def test_range_caffeine_low_bucket() -> None:
    rule = AttributeRule(attribute_key="caffeine_mg", weight=1.0, kind="range")
    assert match_score(rule, "low", 60) == 1.0
    assert match_score(rule, "low", 5) == pytest.approx(0.5, rel=0.1)
    assert match_score(rule, "decaf", 5) == 1.0
    assert match_score(rule, "high", 5) == 0.0


def test_range_invalid_target_returns_zero() -> None:
    rule = AttributeRule(attribute_key="caffeine_mg", weight=1.0, kind="range")
    assert match_score(rule, "nonsense", 100) == 0.0


def test_match_score_handles_missing_value() -> None:
    rule = AttributeRule(attribute_key="anything", weight=1.0, kind="exact")
    assert match_score(rule, "x", None) == 0.0


def test_score_products_ranks_top_match_first() -> None:
    """A user who picks light roast + fruity beats brews a strong-roast espresso."""
    products = [
        {
            "id": 1,
            "attributes": {
                "roast_level": "light",
                "flavor_profile": ["fruity", "floral"],
                "brew_method_compatibility": ["drip"],
            },
        },
        {
            "id": 2,
            "attributes": {
                "roast_level": "dark",
                "flavor_profile": ["earthy"],
                "brew_method_compatibility": ["espresso"],
            },
        },
    ]
    answers = [
        {"question_id": 10, "value": "light"},
        {"question_id": 11, "value": "fruity"},
        {"question_id": 12, "value": "drip"},
    ]
    slug_map = {10: "roast_preference", 11: "flavor_profile", 12: "brew_method"}
    scored = score_products(answers, products, slug_map)
    assert scored[0].product_id == 1
    assert scored[0].score > scored[1].score
    assert scored[0].reasons  # has at least one reason


def test_score_products_tie_break_by_id() -> None:
    products = [
        {"id": 5, "attributes": {"roast_level": "medium"}},
        {"id": 2, "attributes": {"roast_level": "medium"}},
    ]
    answers = [{"question_id": 1, "value": "medium"}]
    slug_map = {1: "roast_preference"}
    scored = score_products(answers, products, slug_map)
    assert scored[0].score == scored[1].score
    assert scored[0].product_id == 2  # lower id wins on tie
    assert scored[1].product_id == 5


def test_score_products_unknown_question_ignored() -> None:
    products = [{"id": 1, "attributes": {"roast_level": "medium"}}]
    answers = [{"question_id": 999, "value": "medium"}]
    slug_map: dict[int, str] = {}
    scored = score_products(answers, products, slug_map)
    assert scored[0].score == 0.0


def test_score_products_empty_answers_yields_zero_scores() -> None:
    products = [{"id": 1, "attributes": {"roast_level": "medium"}}]
    scored = score_products([], products, {})
    assert scored[0].score == 0.0
    assert scored[0].reasons == []

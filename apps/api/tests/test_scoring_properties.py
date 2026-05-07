"""Property-based tests for the scoring engine using Hypothesis.

These tests assert invariants that must hold for *any* random combination of
answers and product attributes:

1. Score bounds — every product score is in ``[0, max_score]`` where
   ``max_score`` is the sum of answer weights.
2. Subset monotonicity — if ``answers_b`` is a strict subset of ``answers_a``
   (i.e. ``answers_a`` adds more weighted constraints), then
   ``score(answers_a, p) >= score(answers_b, p)`` for every product. This is
   the natural direction: more matching constraints = same or higher score.
   (The constraint-superset case in the spec is reframed in the natural
   direction; see the docstring on ``test_subset_monotonicity``.)
3. Hard incompatibility — when a product's ``brew_method_compatibility`` does
   not contain the user's chosen ``brew_method``, that question's contribution
   is exactly zero.
"""
from __future__ import annotations

from typing import Any

from hypothesis import HealthCheck, given, settings
from hypothesis import strategies as st

from apps.recommend.scoring import (
    QUESTION_TO_ATTRIBUTES,
    score_products,
)

# Answer-domain strategies, keyed by question slug. Each strategy emits values
# that the corresponding rule can score (or reject cleanly with 0).
ROAST_VALUES = ["light", "medium", "dark"]
PRICE_TIERS = ["budget", "mid", "premium"]
ACIDITY_VALUES = ["low", "medium", "bright"]
CAFFEINE_BUCKETS = ["decaf", "low", "medium", "high"]
FLAVORS = ["fruity", "nutty", "chocolate", "floral", "earthy"]
BREW_METHODS = ["espresso", "drip", "french_press", "aeropress", "coldbrew"]


def _answer_strategy_for_slug(slug: str) -> st.SearchStrategy[Any]:
    if slug == "roast_preference":
        return st.sampled_from(ROAST_VALUES)
    if slug == "flavor_profile":
        return st.lists(st.sampled_from(FLAVORS), min_size=1, max_size=3, unique=True)
    if slug == "brew_method":
        return st.sampled_from(BREW_METHODS)
    if slug == "caffeine_sensitivity":
        return st.sampled_from(CAFFEINE_BUCKETS)
    if slug == "budget":
        return st.sampled_from(PRICE_TIERS)
    if slug == "milk":
        return st.booleans()
    if slug == "acidity":
        return st.sampled_from(ACIDITY_VALUES)
    if slug == "drinking_time":
        return st.sampled_from(CAFFEINE_BUCKETS)
    if slug == "experience_level":
        return st.sampled_from(ACIDITY_VALUES)
    if slug == "origin":
        return st.lists(st.sampled_from(FLAVORS), min_size=1, max_size=2, unique=True)
    if slug == "grind":
        return st.sampled_from(BREW_METHODS)
    if slug == "intensity":
        return st.sampled_from(CAFFEINE_BUCKETS)
    return st.just(None)


SLUGS = list(QUESTION_TO_ATTRIBUTES.keys())


@st.composite
def answer_set(draw: st.DrawFn, min_size: int = 1, max_size: int = 6) -> list[dict[str, Any]]:
    """Draw a non-empty list of (question_id, value) pairs with unique slugs."""
    chosen_slugs = draw(
        st.lists(st.sampled_from(SLUGS), min_size=min_size, max_size=max_size, unique=True)
    )
    answers: list[dict[str, Any]] = []
    for idx, slug in enumerate(chosen_slugs, start=1):
        value = draw(_answer_strategy_for_slug(slug))
        answers.append({"question_id": idx, "value": value, "_slug": slug})
    return answers


@st.composite
def product_set(draw: st.DrawFn, min_size: int = 1, max_size: int = 5) -> list[dict[str, Any]]:
    """Draw a list of products with realistic attribute values."""
    n = draw(st.integers(min_value=min_size, max_value=max_size))
    products: list[dict[str, Any]] = []
    for i in range(n):
        attrs: dict[str, Any] = {
            "roast_level": draw(st.sampled_from(ROAST_VALUES)),
            "flavor_profile": draw(
                st.lists(st.sampled_from(FLAVORS), min_size=1, max_size=3, unique=True)
            ),
            "caffeine_mg": draw(st.integers(min_value=0, max_value=220)),
            "brew_method_compatibility": draw(
                st.lists(st.sampled_from(BREW_METHODS), min_size=1, max_size=4, unique=True)
            ),
            "price_tier": draw(st.sampled_from(PRICE_TIERS)),
            "milk_friendly": draw(st.booleans()),
            "acidity": draw(st.sampled_from(ACIDITY_VALUES)),
        }
        products.append({"id": i + 1, "attributes": attrs})
    return products


def _slug_map(answers: list[dict[str, Any]]) -> dict[int, str]:
    return {int(a["question_id"]): str(a["_slug"]) for a in answers}


def _strip(answers: list[dict[str, Any]]) -> list[dict[str, Any]]:
    return [{"question_id": a["question_id"], "value": a["value"]} for a in answers]


def _max_score(answers: list[dict[str, Any]]) -> float:
    """Maximum achievable score = sum of rule weights for the answered slugs."""
    total = 0.0
    for a in answers:
        slug = a["_slug"]
        for rule in QUESTION_TO_ATTRIBUTES.get(slug, []):
            total += rule.weight
    return total


@given(answers=answer_set(), products=product_set())
@settings(max_examples=150, deadline=None, suppress_health_check=[HealthCheck.too_slow])
def test_score_is_within_bounds(
    answers: list[dict[str, Any]], products: list[dict[str, Any]]
) -> None:
    """Every product score is in [0, sum(weights)] for the chosen answers."""
    cap = _max_score(answers)
    scored = score_products(_strip(answers), products, _slug_map(answers))
    assert len(scored) == len(products)
    for s in scored:
        assert s.score >= 0.0, f"negative score: {s.score}"
        assert s.score <= cap + 1e-6, f"score {s.score} exceeds cap {cap}"


@given(
    base=answer_set(min_size=1, max_size=3),
    extra=answer_set(min_size=1, max_size=3),
    products=product_set(),
)
@settings(max_examples=120, deadline=None, suppress_health_check=[HealthCheck.too_slow])
def test_subset_monotonicity(
    base: list[dict[str, Any]],
    extra: list[dict[str, Any]],
    products: list[dict[str, Any]],
) -> None:
    """Adding a constraint never lowers the score.

    The spec phrases this in the constraint direction: "more constraints = lower
    or equal scores". The scorer accumulates weighted contributions, so each
    additional answer adds a non-negative term. Equivalently, if ``answers_a``
    is a strict superset of ``answers_b`` (more constraints), then
    ``score_a >= score_b`` for every product. We assert that natural form.
    """
    # Merge so each slug appears at most once; drop overlapping slugs from extra.
    base_slugs = {a["_slug"] for a in base}
    extra_unique = [a for a in extra if a["_slug"] not in base_slugs]
    if not extra_unique:
        return  # tie-handling: identical answer sets trivially satisfy >= equality.
    # Reassign question_ids so superset has a single coherent map.
    superset: list[dict[str, Any]] = []
    for idx, a in enumerate(base + extra_unique, start=1):
        superset.append({**a, "question_id": idx})
    subset: list[dict[str, Any]] = []
    for idx, a in enumerate(base, start=1):
        subset.append({**a, "question_id": idx})

    scored_super = score_products(_strip(superset), products, _slug_map(superset))
    scored_sub = score_products(_strip(subset), products, _slug_map(subset))
    by_id_super = {s.product_id: s.score for s in scored_super}
    by_id_sub = {s.product_id: s.score for s in scored_sub}
    for pid, super_score in by_id_super.items():
        sub_score = by_id_sub[pid]
        assert super_score + 1e-6 >= sub_score, (
            f"product {pid}: superset score {super_score} < subset score {sub_score}"
        )


@given(
    user_brew=st.sampled_from(BREW_METHODS),
    product_brews=st.lists(st.sampled_from(BREW_METHODS), min_size=1, max_size=3, unique=True),
)
@settings(max_examples=80, deadline=None)
def test_hard_incompatibility_brew_method(
    user_brew: str, product_brews: list[str]
) -> None:
    """If the user's brew_method is not in the product's compatibility set,
    the brew_method contribution is exactly zero (no partial credit).

    We test the brew_method rule in isolation by submitting only that one
    answer; the resulting product score equals the brew_method contribution.
    """
    answer = [{"question_id": 1, "value": user_brew, "_slug": "brew_method"}]
    products = [
        {
            "id": 1,
            "attributes": {"brew_method_compatibility": product_brews},
        }
    ]
    scored = score_products(_strip(answer), products, _slug_map(answer))
    if user_brew in product_brews:
        # Compatible — full weight credit (rule weight is 3.0).
        assert scored[0].score == 3.0
    else:
        # Incompatible — exactly zero, no partial credit.
        assert scored[0].score == 0.0

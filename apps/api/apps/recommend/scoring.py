"""Weighted-attribute scoring for the recommendation quiz.

The scorer is a set of pure functions over plain dictionaries. It does not
import Django models or touch the database. The service layer collects data
from the ORM, hands it to ``score_products``, then re-attaches identifiers.

Algorithm
---------
For each (question, target value) supplied by the user, every product earns:

    weight * match_score(target, product_attribute_value)

``match_score`` is:

* 1.0 when the target equals the product attribute (or the target is one of
  the values in a list-valued attribute).
* A linear fall-off for ordinal attributes — overshoot by 1 tier returns 0.5,
  overshoot by 2 returns 0.0.
* 0.0 for hard incompatibility (e.g. the user demands "drip-only" but the
  product is espresso-only).

Each question is mapped to one or more product attributes through
``QUESTION_TO_ATTRIBUTES``. The mapping also declares the kind of comparison
to perform (exact, set-membership, ordinal, range).
"""
from __future__ import annotations

from dataclasses import dataclass
from typing import Any, Literal

# ----------------------------------------------------------------------------
# Question → attribute mapping
# ----------------------------------------------------------------------------

CompareKind = Literal["exact", "membership", "ordinal", "range"]


@dataclass(frozen=True)
class AttributeRule:
    """How a single question's answer is compared to a product attribute."""

    attribute_key: str
    weight: float
    kind: CompareKind
    # Order of values for ordinal comparison (e.g. roast levels).
    ordinal_order: tuple[str, ...] | None = None
    # Human-readable label used in `reasons`.
    label: str = ""


# Ordinal scales used across multiple rules.
ROAST_ORDER: tuple[str, ...] = ("light", "medium", "dark")
PRICE_ORDER: tuple[str, ...] = ("budget", "mid", "premium")
ACIDITY_ORDER: tuple[str, ...] = ("low", "medium", "bright")
CAFFEINE_ORDER: tuple[str, ...] = ("decaf", "low", "medium", "high")

QUESTION_TO_ATTRIBUTES: dict[str, list[AttributeRule]] = {
    "roast_preference": [
        AttributeRule(
            attribute_key="roast_level",
            weight=2.0,
            kind="ordinal",
            ordinal_order=ROAST_ORDER,
            label="roast level",
        ),
    ],
    "flavor_profile": [
        AttributeRule(
            attribute_key="flavor_profile",
            weight=2.0,
            kind="membership",
            label="flavor profile",
        ),
    ],
    "brew_method": [
        AttributeRule(
            attribute_key="brew_method_compatibility",
            weight=3.0,
            kind="membership",
            label="brew method",
        ),
    ],
    "caffeine_sensitivity": [
        AttributeRule(
            attribute_key="caffeine_mg",
            weight=1.5,
            kind="range",
            label="caffeine level",
        ),
    ],
    "budget": [
        AttributeRule(
            attribute_key="price_tier",
            weight=2.0,
            kind="ordinal",
            ordinal_order=PRICE_ORDER,
            label="budget",
        ),
    ],
    "milk": [
        AttributeRule(
            attribute_key="milk_friendly",
            weight=1.0,
            kind="exact",
            label="milk pairing",
        ),
    ],
    "acidity": [
        AttributeRule(
            attribute_key="acidity",
            weight=1.0,
            kind="ordinal",
            ordinal_order=ACIDITY_ORDER,
            label="acidity",
        ),
    ],
    "drinking_time": [
        AttributeRule(
            attribute_key="caffeine_mg",
            weight=1.0,
            kind="range",
            label="time-of-day caffeine",
        ),
    ],
    "experience_level": [
        AttributeRule(
            attribute_key="acidity",
            weight=0.5,
            kind="ordinal",
            ordinal_order=ACIDITY_ORDER,
            label="experience-level acidity",
        ),
    ],
    "origin": [
        AttributeRule(
            attribute_key="flavor_profile",
            weight=1.0,
            kind="membership",
            label="origin / flavor",
        ),
    ],
    "grind": [
        AttributeRule(
            attribute_key="brew_method_compatibility",
            weight=0.5,
            kind="membership",
            label="grind / brew compatibility",
        ),
    ],
    "intensity": [
        AttributeRule(
            attribute_key="caffeine_mg",
            weight=1.0,
            kind="range",
            label="intensity",
        ),
    ],
}

# Caffeine target ranges (mg per serving) for ordinal "intensity"-style answers.
CAFFEINE_TARGETS: dict[str, tuple[int, int]] = {
    "decaf": (0, 30),
    "low": (30, 80),
    "medium": (80, 130),
    "high": (130, 220),
}


# ----------------------------------------------------------------------------
# Match scoring primitives
# ----------------------------------------------------------------------------


def _score_exact(target: Any, value: Any) -> float:
    return 1.0 if target == value else 0.0


def _score_membership(target: Any, value: Any) -> float:
    """Target may be scalar or list. Value may be scalar or list. Any overlap → 1.0."""
    target_set = set(target) if isinstance(target, list) else {target}
    value_set = set(value) if isinstance(value, list) else {value}
    if target_set & value_set:
        return 1.0
    return 0.0


def _score_ordinal(target: Any, value: Any, order: tuple[str, ...]) -> float:
    if target not in order or value not in order:
        return 0.0
    distance = abs(order.index(target) - order.index(value))
    if distance == 0:
        return 1.0
    if distance == 1:
        return 0.5
    return 0.0


def _score_range(target: Any, value: Any) -> float:
    """Target is an ordinal label mapped to a (min,max) range; value is a number."""
    if isinstance(target, str):
        bounds = CAFFEINE_TARGETS.get(target)
    elif isinstance(target, list | tuple) and len(target) == 2:
        bounds = (int(target[0]), int(target[1]))
    else:
        bounds = None
    if bounds is None:
        return 0.0
    try:
        numeric = float(value)
    except (TypeError, ValueError):
        return 0.0
    lo, hi = bounds
    if lo <= numeric <= hi:
        return 1.0
    span = max(hi - lo, 1)
    over = numeric - hi if numeric > hi else lo - numeric
    fall_off = over / span
    if fall_off <= 1.0:
        return max(0.0, 1.0 - fall_off)
    return 0.0


def match_score(rule: AttributeRule, target: Any, value: Any) -> float:
    """Dispatch to the appropriate primitive based on rule kind."""
    if value is None:
        return 0.0
    if rule.kind == "exact":
        return _score_exact(target, value)
    if rule.kind == "membership":
        return _score_membership(target, value)
    if rule.kind == "ordinal":
        if rule.ordinal_order is None:
            return 0.0
        return _score_ordinal(target, value, rule.ordinal_order)
    if rule.kind == "range":
        return _score_range(target, value)
    return 0.0


# ----------------------------------------------------------------------------
# Aggregate scoring
# ----------------------------------------------------------------------------


@dataclass
class ScoredProduct:
    product_id: int
    score: float
    reasons: list[str]


def score_products(
    answers: list[dict[str, Any]],
    products: list[dict[str, Any]],
    question_slug_by_id: dict[int, str],
) -> list[ScoredProduct]:
    """Score every product against the supplied answers.

    Parameters
    ----------
    answers
        ``[{"question_id": int, "value": Any}]`` from the user.
    products
        ``[{"id": int, "attributes": {key: value}}]``.
    question_slug_by_id
        Maps ``question_id`` to its slug, which is used to look up the rules.

    Returns
    -------
    A list of ``ScoredProduct`` sorted by descending score, then ascending id.
    """
    results: list[ScoredProduct] = []
    for product in products:
        attrs: dict[str, Any] = product.get("attributes", {})
        contributions: list[tuple[float, str]] = []
        total = 0.0
        for answer in answers:
            qid = int(answer["question_id"])
            slug = question_slug_by_id.get(qid)
            if slug is None:
                continue
            rules = QUESTION_TO_ATTRIBUTES.get(slug, [])
            for rule in rules:
                value = attrs.get(rule.attribute_key)
                contribution = rule.weight * match_score(rule, answer["value"], value)
                if contribution > 0:
                    contributions.append((contribution, rule.label or rule.attribute_key))
                total += contribution
        contributions.sort(key=lambda pair: pair[0], reverse=True)
        reasons = [f"matches your {label}" for _, label in contributions[:3]]
        results.append(
            ScoredProduct(
                product_id=int(product["id"]),
                score=round(total, 4),
                reasons=reasons,
            )
        )

    results.sort(key=lambda r: (-r.score, r.product_id))
    return results

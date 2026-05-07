"""A/B-test scoring variants and persisted quiz submissions.

A ``ScoringVariant`` captures a named weight configuration (per question slug),
plus a flag describing how budget overruns are handled. Submissions reference
the variant they were scored against so we can do offline analysis (which
variant produced higher mean scores, which products it recommended most often,
etc.).
"""
from __future__ import annotations

from typing import Any

from django.db import models


class ScoringVariant(models.Model):
    """A named scoring configuration.

    ``weights`` is a JSON object keyed by question slug (e.g.
    ``{"flavor_profile": 4.0}``). Slugs not in ``weights`` fall back to the
    rule's default weight.

    ``hard_fail_keys`` is a list of question slugs whose mismatch should
    short-circuit the product to score 0 instead of accumulating partial
    credit (used by the ``budget_strict`` variant).
    """

    name = models.CharField(max_length=64, unique=True)
    description = models.CharField(max_length=255, blank=True, default="")
    weights = models.JSONField(default=dict, blank=True)
    hard_fail_keys = models.JSONField(default=list, blank=True)
    is_active = models.BooleanField(default=True)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ["name"]

    def __str__(self) -> str:
        return f"variant:{self.name}"

    def weight_overrides(self) -> dict[str, float]:
        """Type-safe accessor used by the scorer."""
        raw: Any = self.weights or {}
        if not isinstance(raw, dict):
            return {}
        out: dict[str, float] = {}
        for k, v in raw.items():
            try:
                out[str(k)] = float(v)
            except (TypeError, ValueError):
                continue
        return out

    def hard_fail_slugs(self) -> list[str]:
        raw: Any = self.hard_fail_keys or []
        if not isinstance(raw, list):
            return []
        return [str(x) for x in raw]


class QuizSubmission(models.Model):
    """A single user's submitted answer set + recommendation snapshot."""

    variant = models.ForeignKey(
        ScoringVariant,
        on_delete=models.PROTECT,
        related_name="submissions",
    )
    answers = models.JSONField()
    recommendations = models.JSONField()
    session_id = models.CharField(max_length=64, blank=True, default="")
    submitted_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ["-submitted_at", "-id"]
        indexes = [
            models.Index(fields=["variant", "-submitted_at"]),
        ]

    def __str__(self) -> str:
        return f"submission:{self.id}@{self.variant.name}"

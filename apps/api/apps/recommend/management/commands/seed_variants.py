"""Seed three reference scoring variants used by the A/B harness."""
from __future__ import annotations

from typing import Any

from django.core.management.base import BaseCommand
from django.db import transaction

from apps.recommend.models import ScoringVariant

VARIANTS: list[dict[str, Any]] = [
    {
        "name": "default",
        "description": "Baseline weights as declared in scoring.QUESTION_TO_ATTRIBUTES.",
        "weights": {},
        "hard_fail_keys": [],
    },
    {
        "name": "flavor_heavy",
        "description": "Doubles the flavor_profile rule weight; everything else default.",
        "weights": {"flavor_profile": 2.0},
        "hard_fail_keys": [],
    },
    {
        "name": "budget_strict",
        "description": "Hard-rejects products that mismatch the budget bucket.",
        "weights": {},
        "hard_fail_keys": ["budget"],
    },
]


class Command(BaseCommand):
    help = "Seed the three reference scoring variants (default, flavor_heavy, budget_strict)."

    def handle(self, *args: Any, **options: Any) -> None:
        with transaction.atomic():
            for spec in VARIANTS:
                ScoringVariant.objects.update_or_create(
                    name=spec["name"],
                    defaults={
                        "description": spec["description"],
                        "weights": spec["weights"],
                        "hard_fail_keys": spec["hard_fail_keys"],
                        "is_active": True,
                    },
                )
        self.stdout.write(self.style.SUCCESS(f"Seeded {len(VARIANTS)} variants."))

"""Smoke test for the seed_catalog management command."""
from __future__ import annotations

import pytest
from django.core.management import call_command

from apps.catalog.models import Product
from apps.quiz.models import Question

pytestmark = pytest.mark.django_db


def test_seed_command_loads_questions_and_products() -> None:
    call_command("seed_catalog")
    assert Question.objects.count() == 12
    assert Product.objects.count() == 30
    # Idempotent: second run should not duplicate.
    call_command("seed_catalog")
    assert Question.objects.count() == 12
    assert Product.objects.count() == 30


def test_factories_can_create_models() -> None:
    from tests.factories import AnswerOptionFactory, ProductAttributeFactory

    option = AnswerOptionFactory()
    assert option.id is not None
    attr = ProductAttributeFactory()
    assert attr.id is not None

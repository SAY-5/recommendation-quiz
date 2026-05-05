"""Factory Boy factories for tests."""
from __future__ import annotations

from typing import Any

import factory
from factory.django import DjangoModelFactory

from apps.catalog.models import Product, ProductAttribute
from apps.quiz.models import AnswerOption, Question, QuestionKind


class QuestionFactory(DjangoModelFactory):
    class Meta:
        model = Question

    slug = factory.Sequence(lambda n: f"question-{n}")
    prompt = factory.Faker("sentence", nb_words=6)
    order = factory.Sequence(lambda n: n)
    kind = QuestionKind.SINGLE


class AnswerOptionFactory(DjangoModelFactory):
    class Meta:
        model = AnswerOption

    question = factory.SubFactory(QuestionFactory)
    value = factory.Sequence(lambda n: f"opt-{n}")
    label = factory.Faker("word")
    order = factory.Sequence(lambda n: n)


class ProductFactory(DjangoModelFactory):
    class Meta:
        model = Product

    name = factory.Sequence(lambda n: f"Coffee {n}")
    brand = factory.Faker("company")
    price_cents = 1500
    image_url = ""


class ProductAttributeFactory(DjangoModelFactory):
    class Meta:
        model = ProductAttribute

    product = factory.SubFactory(ProductFactory)
    key = "roast_level"
    value: Any = "medium"

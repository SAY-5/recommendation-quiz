"""Quiz domain models: Question and AnswerOption."""
from __future__ import annotations

from django.db import models


class QuestionKind(models.TextChoices):
    SINGLE = "single", "Single choice"
    MULTI = "multi", "Multi choice"
    RANGE = "range", "Range / ordinal"


class Question(models.Model):
    slug = models.SlugField(max_length=64, unique=True)
    prompt = models.CharField(max_length=255)
    order = models.PositiveIntegerField(default=0)
    kind = models.CharField(
        max_length=16,
        choices=QuestionKind.choices,
        default=QuestionKind.SINGLE,
    )

    class Meta:
        ordering = ["order", "id"]

    def __str__(self) -> str:
        return f"{self.order:02d}. {self.prompt}"


class AnswerOption(models.Model):
    question = models.ForeignKey(
        Question,
        on_delete=models.CASCADE,
        related_name="options",
    )
    value = models.CharField(max_length=64)
    label = models.CharField(max_length=128)
    order = models.PositiveIntegerField(default=0)

    class Meta:
        ordering = ["order", "id"]
        constraints = [
            models.UniqueConstraint(
                fields=["question", "value"],
                name="unique_option_value_per_question",
            ),
        ]

    def __str__(self) -> str:
        return f"{self.question.slug}={self.value}"

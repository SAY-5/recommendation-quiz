"""Serializers for variants and submissions."""
from __future__ import annotations

from typing import Any

from rest_framework import serializers

from .models import QuizSubmission, ScoringVariant


class ScoringVariantSerializer(serializers.ModelSerializer[ScoringVariant]):
    class Meta:
        model = ScoringVariant
        fields = (
            "id",
            "name",
            "description",
            "weights",
            "hard_fail_keys",
            "is_active",
            "created_at",
        )
        read_only_fields = ("id", "created_at")


class ScoringVariantCreateSerializer(serializers.Serializer[dict[str, Any]]):
    name = serializers.RegexField(regex=r"^[a-z][a-z0-9_]*$", max_length=64)
    description = serializers.CharField(max_length=255, required=False, allow_blank=True)
    weights = serializers.JSONField(required=False)
    hard_fail_keys = serializers.ListField(
        child=serializers.CharField(max_length=64), required=False
    )
    is_active = serializers.BooleanField(required=False, default=True)


class QuizSubmissionSerializer(serializers.ModelSerializer[QuizSubmission]):
    variant_name = serializers.CharField(source="variant.name", read_only=True)

    class Meta:
        model = QuizSubmission
        fields = (
            "id",
            "variant",
            "variant_name",
            "answers",
            "recommendations",
            "session_id",
            "submitted_at",
        )
        read_only_fields = fields

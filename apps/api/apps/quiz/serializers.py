"""Serializers for quiz questions, options, and the score endpoint payloads."""
from __future__ import annotations

from typing import Any

from rest_framework import serializers

from .models import AnswerOption, Question


class AnswerOptionSerializer(serializers.ModelSerializer[AnswerOption]):
    class Meta:
        model = AnswerOption
        fields = ("value", "label", "order")


class QuestionSerializer(serializers.ModelSerializer[Question]):
    options = AnswerOptionSerializer(many=True, read_only=True)

    class Meta:
        model = Question
        fields = ("id", "slug", "prompt", "order", "kind", "options")


class AnswerInputSerializer(serializers.Serializer[dict[str, Any]]):
    question_id = serializers.IntegerField(min_value=1)
    value = serializers.JSONField()


class ScoreRequestSerializer(serializers.Serializer[dict[str, Any]]):
    answers = AnswerInputSerializer(many=True, allow_empty=False)


class ProductBriefSerializer(serializers.Serializer[dict[str, Any]]):
    id = serializers.IntegerField()
    name = serializers.CharField()
    brand = serializers.CharField()
    price_cents = serializers.IntegerField()
    image_url = serializers.URLField(allow_blank=True)


class QuestionContributionSerializer(serializers.Serializer[dict[str, Any]]):
    question_id = serializers.IntegerField()
    question_prompt = serializers.CharField()
    user_answer = serializers.JSONField()
    contribution_pts = serializers.FloatField()
    max_contribution_pts = serializers.FloatField()
    why = serializers.CharField()


class RecommendationSerializer(serializers.Serializer[dict[str, Any]]):
    product = ProductBriefSerializer()
    score = serializers.FloatField()
    reasons = serializers.ListField(child=serializers.CharField())
    breakdown = QuestionContributionSerializer(many=True, required=False)


class ScoreResponseSerializer(serializers.Serializer[dict[str, Any]]):
    recommendations = RecommendationSerializer(many=True)

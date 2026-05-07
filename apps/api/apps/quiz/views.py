"""Quiz endpoints: list questions, score answers."""
from __future__ import annotations

from typing import Any

from drf_spectacular.utils import OpenApiParameter, OpenApiResponse, extend_schema
from rest_framework import status
from rest_framework.request import Request
from rest_framework.response import Response
from rest_framework.views import APIView

from apps.recommend.service import recommend_top_n

from .models import Question
from .serializers import (
    QuestionSerializer,
    ScoreRequestSerializer,
    ScoreResponseSerializer,
)


class QuestionListView(APIView):
    """Return all quiz questions in display order, with options."""

    @extend_schema(
        responses={200: QuestionSerializer(many=True)},
        description="Full ordered list of quiz questions and their answer options.",
    )
    def get(self, request: Request) -> Response:
        questions = Question.objects.prefetch_related("options").all()
        data = QuestionSerializer(questions, many=True).data
        return Response(data, status=status.HTTP_200_OK)


class ScoreView(APIView):
    """Score the user's answers against the catalog and return top recommendations."""

    @extend_schema(
        request=ScoreRequestSerializer,
        responses={
            200: ScoreResponseSerializer,
            400: OpenApiResponse(description="Validation error envelope."),
        },
        parameters=[
            OpenApiParameter(
                name="variant",
                description="Scoring variant name; falls back to 'default'.",
                required=False,
                type=str,
            ),
        ],
        description="Compute weighted-attribute scores and return the top-3 recommendations.",
    )
    def post(self, request: Request) -> Response:
        serializer = ScoreRequestSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        answers: list[dict[str, Any]] = serializer.validated_data["answers"]
        variant = request.query_params.get("variant")
        session_id = request.headers.get("X-Session-Id", "")
        recommendations = recommend_top_n(
            answers,
            top_n=3,
            variant_name=variant,
            persist=True,
            session_id=session_id,
        )
        return Response({"recommendations": recommendations}, status=status.HTTP_200_OK)

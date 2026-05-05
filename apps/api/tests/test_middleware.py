"""Test the request-id middleware."""
from __future__ import annotations

import pytest

from apps.quiz.models import Question

pytestmark = pytest.mark.django_db


def test_request_id_header_round_trip(api_client) -> None:
    Question.objects.create(slug="dummy", prompt="hi", order=1, kind="single")
    response = api_client.get("/api/quiz/questions", HTTP_X_REQUEST_ID="abc-123")
    assert response.headers["X-Request-ID"] == "abc-123"


def test_request_id_generated_when_missing(api_client) -> None:
    Question.objects.create(slug="dummy2", prompt="hi", order=1, kind="single")
    response = api_client.get("/api/quiz/questions")
    assert "X-Request-ID" in response.headers
    assert len(response.headers["X-Request-ID"]) > 0

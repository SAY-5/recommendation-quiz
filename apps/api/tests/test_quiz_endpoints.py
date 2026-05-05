"""Integration tests for the quiz endpoints."""
from __future__ import annotations

import pytest

from apps.catalog.models import Product, ProductAttribute
from apps.quiz.models import AnswerOption, Question

pytestmark = pytest.mark.django_db


def _build_seed() -> dict[str, int]:
    q_roast = Question.objects.create(
        slug="roast_preference", prompt="Roast?", order=1, kind="single"
    )
    AnswerOption.objects.create(question=q_roast, value="light", label="Light", order=1)
    AnswerOption.objects.create(question=q_roast, value="medium", label="Medium", order=2)

    q_brew = Question.objects.create(slug="brew_method", prompt="Brew?", order=2, kind="single")
    AnswerOption.objects.create(question=q_brew, value="drip", label="Drip", order=1)
    AnswerOption.objects.create(question=q_brew, value="espresso", label="Espresso", order=2)

    p1 = Product.objects.create(name="Light Drip", brand="Acme", price_cents=1500)
    ProductAttribute.objects.create(product=p1, key="roast_level", value="light")
    ProductAttribute.objects.create(
        product=p1, key="brew_method_compatibility", value=["drip", "aeropress"]
    )

    p2 = Product.objects.create(name="Dark Shot", brand="Acme", price_cents=1800)
    ProductAttribute.objects.create(product=p2, key="roast_level", value="dark")
    ProductAttribute.objects.create(
        product=p2, key="brew_method_compatibility", value=["espresso"]
    )

    return {
        "q_roast": q_roast.id,
        "q_brew": q_brew.id,
        "p_light": p1.id,
        "p_dark": p2.id,
    }


def test_questions_endpoint_returns_ordered_list(api_client) -> None:
    _build_seed()
    response = api_client.get("/api/quiz/questions")
    assert response.status_code == 200
    body = response.json()
    assert [q["slug"] for q in body] == ["roast_preference", "brew_method"]
    assert len(body[0]["options"]) == 2


def test_score_endpoint_returns_top_match(api_client) -> None:
    ids = _build_seed()
    response = api_client.post(
        "/api/quiz/score",
        data={
            "answers": [
                {"question_id": ids["q_roast"], "value": "light"},
                {"question_id": ids["q_brew"], "value": "drip"},
            ]
        },
        format="json",
    )
    assert response.status_code == 200
    recs = response.json()["recommendations"]
    assert recs, "expected at least one recommendation"
    assert recs[0]["product"]["id"] == ids["p_light"]
    assert recs[0]["score"] > 0
    assert isinstance(recs[0]["reasons"], list)


def test_score_endpoint_validation_envelope(api_client) -> None:
    response = api_client.post("/api/quiz/score", data={"answers": []}, format="json")
    assert response.status_code == 400
    body = response.json()
    assert "code" in body
    assert "message" in body
    assert "retryable" in body
    assert "request_id" in body


def test_product_detail(api_client) -> None:
    ids = _build_seed()
    response = api_client.get(f"/api/products/{ids['p_light']}")
    assert response.status_code == 200
    body = response.json()
    assert body["name"] == "Light Drip"
    assert any(a["key"] == "roast_level" for a in body["attributes"])

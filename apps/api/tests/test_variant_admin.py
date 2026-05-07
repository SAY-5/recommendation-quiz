"""Tests for the /api/admin/variants admin endpoints (token-gated)."""
from __future__ import annotations

import pytest

from apps.catalog.models import Product, ProductAttribute
from apps.quiz.models import AnswerOption, Question
from apps.recommend.models import QuizSubmission, ScoringVariant

pytestmark = pytest.mark.django_db


ADMIN_TOKEN = "test-admin-token"


@pytest.fixture(autouse=True)
def _admin_token_env(monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.setenv("ADMIN_API_TOKEN", ADMIN_TOKEN)


def _auth_headers() -> dict[str, str]:
    return {"HTTP_AUTHORIZATION": f"Bearer {ADMIN_TOKEN}"}


def _seed() -> dict[str, int]:
    q = Question.objects.create(
        slug="roast_preference", prompt="Roast?", order=1, kind="single"
    )
    AnswerOption.objects.create(question=q, value="light", label="Light", order=1)
    AnswerOption.objects.create(question=q, value="medium", label="Medium", order=2)
    p1 = Product.objects.create(name="P1", brand="Acme", price_cents=1500)
    ProductAttribute.objects.create(product=p1, key="roast_level", value="light")
    p2 = Product.objects.create(name="P2", brand="Acme", price_cents=1800)
    ProductAttribute.objects.create(product=p2, key="roast_level", value="medium")
    default = ScoringVariant.objects.create(name="default", weights={}, hard_fail_keys=[])
    flavor = ScoringVariant.objects.create(
        name="flavor_heavy", weights={"flavor_profile": 2.0}, hard_fail_keys=[]
    )
    return {
        "q": q.id,
        "p1": p1.id,
        "p2": p2.id,
        "default": default.id,
        "flavor": flavor.id,
    }


def test_admin_variants_requires_token(api_client) -> None:
    resp = api_client.get("/api/admin/variants")
    assert resp.status_code == 403


def test_admin_variants_rejects_wrong_token(api_client) -> None:
    resp = api_client.get(
        "/api/admin/variants",
        HTTP_AUTHORIZATION="Bearer wrong",
    )
    assert resp.status_code == 403


def test_admin_variants_returns_403_when_token_unset(
    api_client, monkeypatch: pytest.MonkeyPatch
) -> None:
    monkeypatch.delenv("ADMIN_API_TOKEN", raising=False)
    resp = api_client.get(
        "/api/admin/variants",
        HTTP_AUTHORIZATION="Bearer anything",
    )
    assert resp.status_code == 403


def test_admin_get_variants_returns_seeded_rows(api_client) -> None:
    _seed()
    resp = api_client.get("/api/admin/variants", **_auth_headers())
    assert resp.status_code == 200
    names = {row["name"] for row in resp.json()}
    assert names == {"default", "flavor_heavy"}


def test_admin_create_variant_persists_and_returns_201(api_client) -> None:
    resp = api_client.post(
        "/api/admin/variants",
        data={
            "name": "experimental_v1",
            "description": "test variant",
            "weights": {"acidity": 3.0},
            "hard_fail_keys": [],
        },
        format="json",
        **_auth_headers(),
    )
    assert resp.status_code == 201
    assert ScoringVariant.objects.filter(name="experimental_v1").exists()


def test_variant_results_paginates_and_returns_404_for_unknown_id(
    api_client,
) -> None:
    ids = _seed()
    qs_payload = [
        {"question_id": ids["q"], "value": "light"},
    ]
    # Submit a few; this hits the persisted-submission path.
    for _ in range(3):
        api_client.post("/api/quiz/score", data={"answers": qs_payload}, format="json")
    resp = api_client.get(
        f"/api/admin/variants/{ids['default']}/results",
        **_auth_headers(),
    )
    assert resp.status_code == 200
    body = resp.json()
    assert len(body["results"]) == 3
    # 404 for unknown id.
    bad = api_client.get("/api/admin/variants/99999/results", **_auth_headers())
    assert bad.status_code == 404


def test_variant_results_pagination_with_cursor(api_client) -> None:
    ids = _seed()
    qs_payload = [{"question_id": ids["q"], "value": "light"}]
    for _ in range(5):
        api_client.post("/api/quiz/score", data={"answers": qs_payload}, format="json")
    resp = api_client.get(
        f"/api/admin/variants/{ids['default']}/results?page_size=2",
        **_auth_headers(),
    )
    assert resp.status_code == 200
    page1 = resp.json()
    assert len(page1["results"]) == 2
    assert page1["next_cursor"] is not None
    resp2 = api_client.get(
        f"/api/admin/variants/{ids['default']}/results"
        f"?page_size=2&cursor={page1['next_cursor']}",
        **_auth_headers(),
    )
    assert resp2.status_code == 200
    assert len(resp2.json()["results"]) <= 2


def test_variant_compare_returns_aggregates_for_two_variants(api_client) -> None:
    ids = _seed()
    qs_payload = [{"question_id": ids["q"], "value": "light"}]
    # 3 submissions to default, 2 to flavor_heavy.
    for _ in range(3):
        api_client.post("/api/quiz/score", data={"answers": qs_payload}, format="json")
    for _ in range(2):
        api_client.post(
            "/api/quiz/score?variant=flavor_heavy",
            data={"answers": qs_payload},
            format="json",
        )
    resp = api_client.get(
        f"/api/admin/variants/compare?a={ids['default']}&b={ids['flavor']}",
        **_auth_headers(),
    )
    assert resp.status_code == 200
    body = resp.json()
    assert body["a"]["variant_name"] == "default"
    assert body["a"]["submission_count"] == 3
    assert body["b"]["variant_name"] == "flavor_heavy"
    assert body["b"]["submission_count"] == 2
    assert "top_product_distribution" in body["a"]
    assert "shared_session_score_gap" in body


def test_variant_compare_validates_query_params(api_client) -> None:
    _seed()
    resp = api_client.get("/api/admin/variants/compare", **_auth_headers())
    assert resp.status_code == 400
    resp = api_client.get(
        "/api/admin/variants/compare?a=99999&b=99998",
        **_auth_headers(),
    )
    assert resp.status_code == 404


def test_variant_compare_shared_session_score_gap(api_client) -> None:
    """Submissions with the same X-Session-Id under both variants → score gap."""
    ids = _seed()
    qs_payload = [{"question_id": ids["q"], "value": "light"}]
    sess = "session-abc"
    api_client.post(
        "/api/quiz/score",
        data={"answers": qs_payload},
        format="json",
        HTTP_X_SESSION_ID=sess,
    )
    api_client.post(
        "/api/quiz/score?variant=flavor_heavy",
        data={"answers": qs_payload},
        format="json",
        HTTP_X_SESSION_ID=sess,
    )
    assert (
        QuizSubmission.objects.filter(session_id=sess).count() == 2
    ), "both submissions persisted under the same session"
    resp = api_client.get(
        f"/api/admin/variants/compare?a={ids['default']}&b={ids['flavor']}",
        **_auth_headers(),
    )
    body = resp.json()
    gap = body["shared_session_score_gap"]
    assert gap["shared_session_count"] == 1
    assert gap["mean_top_score_gap_a_minus_b"] is not None


def test_seed_variants_command_is_idempotent(api_client) -> None:
    """Running seed_variants twice should not duplicate rows."""
    from django.core.management import call_command

    call_command("seed_variants")
    first = ScoringVariant.objects.count()
    call_command("seed_variants")
    second = ScoringVariant.objects.count()
    assert first == second == 3

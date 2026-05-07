"""Admin endpoints for the A/B variant harness."""
from __future__ import annotations

import os
from collections import Counter
from typing import Any

from django.db.models import Count
from django.utils.dateparse import parse_datetime
from drf_spectacular.utils import OpenApiParameter, extend_schema
from rest_framework import status
from rest_framework.exceptions import PermissionDenied
from rest_framework.request import Request
from rest_framework.response import Response
from rest_framework.views import APIView

from .models import QuizSubmission, ScoringVariant
from .serializers import (
    QuizSubmissionSerializer,
    ScoringVariantCreateSerializer,
    ScoringVariantSerializer,
)

ADMIN_TOKEN_ENV = "ADMIN_API_TOKEN"
DEFAULT_PAGE_SIZE = 50
MAX_PAGE_SIZE = 200


def _require_admin_token(request: Request) -> None:
    """Reject requests that don't carry the admin token.

    The token is configured via the ``ADMIN_API_TOKEN`` env var. If it is
    unset, admin endpoints are disabled (returns 403). The header is
    ``Authorization: Bearer <token>``.
    """
    expected = os.environ.get(ADMIN_TOKEN_ENV, "").strip()
    if not expected:
        raise PermissionDenied("admin token not configured")
    auth = request.headers.get("Authorization", "")
    if not auth.startswith("Bearer "):
        raise PermissionDenied("missing bearer token")
    presented = auth[len("Bearer ") :].strip()
    if presented != expected:
        raise PermissionDenied("invalid admin token")


class VariantListCreateView(APIView):
    """``GET`` returns variants; ``POST`` creates a new variant."""

    @extend_schema(responses={200: ScoringVariantSerializer(many=True)})
    def get(self, request: Request) -> Response:
        _require_admin_token(request)
        variants = ScoringVariant.objects.all()
        return Response(ScoringVariantSerializer(variants, many=True).data)

    @extend_schema(request=ScoringVariantCreateSerializer, responses={201: ScoringVariantSerializer})
    def post(self, request: Request) -> Response:
        _require_admin_token(request)
        serializer = ScoringVariantCreateSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        data = serializer.validated_data
        variant, _created = ScoringVariant.objects.update_or_create(
            name=data["name"],
            defaults={
                "description": data.get("description", ""),
                "weights": data.get("weights", {}),
                "hard_fail_keys": data.get("hard_fail_keys", []),
                "is_active": data.get("is_active", True),
            },
        )
        return Response(
            ScoringVariantSerializer(variant).data,
            status=status.HTTP_201_CREATED,
        )


class VariantResultsView(APIView):
    """Recent submissions for a variant, cursor-paginated by submitted_at."""

    @extend_schema(
        parameters=[
            OpenApiParameter(name="cursor", required=False, type=str),
            OpenApiParameter(name="page_size", required=False, type=int),
        ],
        responses={200: QuizSubmissionSerializer(many=True)},
    )
    def get(self, request: Request, variant_id: int) -> Response:
        _require_admin_token(request)
        variant = ScoringVariant.objects.filter(id=variant_id).first()
        if variant is None:
            return Response(
                {"detail": "variant not found"}, status=status.HTTP_404_NOT_FOUND
            )
        page_size = min(
            int(request.query_params.get("page_size", DEFAULT_PAGE_SIZE)),
            MAX_PAGE_SIZE,
        )
        qs = QuizSubmission.objects.filter(variant=variant)
        cursor = request.query_params.get("cursor")
        if cursor:
            cutoff = parse_datetime(cursor)
            if cutoff is not None:
                qs = qs.filter(submitted_at__lt=cutoff)
        rows = list(qs[: page_size + 1])
        next_cursor: str | None = None
        if len(rows) > page_size:
            next_cursor = rows[page_size - 1].submitted_at.isoformat()
            rows = rows[:page_size]
        return Response(
            {
                "results": QuizSubmissionSerializer(rows, many=True).data,
                "next_cursor": next_cursor,
            }
        )


class VariantCompareView(APIView):
    """Side-by-side aggregate metrics for two variants."""

    @extend_schema(
        parameters=[
            OpenApiParameter(name="a", required=True, type=int),
            OpenApiParameter(name="b", required=True, type=int),
        ],
    )
    def get(self, request: Request) -> Response:
        _require_admin_token(request)
        try:
            a_id = int(request.query_params["a"])
            b_id = int(request.query_params["b"])
        except (KeyError, ValueError, TypeError):
            return Response(
                {"detail": "a and b query params (variant ids) are required"},
                status=status.HTTP_400_BAD_REQUEST,
            )
        a = ScoringVariant.objects.filter(id=a_id).first()
        b = ScoringVariant.objects.filter(id=b_id).first()
        if a is None or b is None:
            return Response(
                {"detail": "variant not found"},
                status=status.HTTP_404_NOT_FOUND,
            )
        return Response(
            {
                "a": _aggregate(a),
                "b": _aggregate(b),
                "shared_session_score_gap": _shared_session_score_gap(a, b),
            }
        )


def _aggregate(variant: ScoringVariant) -> dict[str, Any]:
    qs = QuizSubmission.objects.filter(variant=variant)
    summary = qs.aggregate(submission_count=Count("id"))
    top_product_distribution = _distribution_top_recommended(qs)
    # Top-score mean is computed in Python: ``recommendations`` is a JSONField
    # holding a list-of-dicts whose shape is portable across sqlite + postgres
    # only via ORM JSON path queries that are dialect-specific. The cost is
    # bounded by ``submission_count`` and is acceptable for an admin endpoint.
    scores = [_top_score(r) for r in qs.values_list("recommendations", flat=True)]
    nonzero = [s for s in scores if s > 0]
    mean_top = round(sum(nonzero) / len(nonzero), 4) if nonzero else None
    return {
        "variant_id": variant.id,
        "variant_name": variant.name,
        "submission_count": int(summary["submission_count"] or 0),
        "top_product_distribution": top_product_distribution,
        "mean_top_score": mean_top,
    }


def _distribution_top_recommended(qs: Any) -> list[dict[str, Any]]:
    counter: Counter[int] = Counter()
    for row in qs.values_list("recommendations", flat=True):
        if isinstance(row, list) and row:
            top = row[0]
            if isinstance(top, dict):
                product = top.get("product") or {}
                pid = product.get("id")
                if isinstance(pid, int):
                    counter[pid] += 1
    return [{"product_id": pid, "count": cnt} for pid, cnt in counter.most_common(10)]


def _shared_session_score_gap(a: ScoringVariant, b: ScoringVariant) -> dict[str, Any]:
    """Mean top-score gap on submissions sharing a session_id across the two variants."""
    a_subs = {
        row.session_id: row.recommendations
        for row in QuizSubmission.objects.filter(variant=a).exclude(session_id="")
    }
    b_subs = {
        row.session_id: row.recommendations
        for row in QuizSubmission.objects.filter(variant=b).exclude(session_id="")
    }
    shared = set(a_subs) & set(b_subs)
    if not shared:
        return {"shared_session_count": 0, "mean_top_score_gap_a_minus_b": None}
    total = 0.0
    n = 0
    for sid in shared:
        a_top = _top_score(a_subs[sid])
        b_top = _top_score(b_subs[sid])
        total += a_top - b_top
        n += 1
    return {
        "shared_session_count": n,
        "mean_top_score_gap_a_minus_b": round(total / n, 4),
    }


def _top_score(recs: Any) -> float:
    if isinstance(recs, list) and recs:
        first = recs[0]
        if isinstance(first, dict):
            score = first.get("score")
            if isinstance(score, int | float):
                return float(score)
    return 0.0



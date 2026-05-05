"""Attach a request_id to every request for error correlation."""
from __future__ import annotations

import uuid
from collections.abc import Callable

from django.http import HttpRequest, HttpResponse


class RequestIdMiddleware:
    """Adds a unique X-Request-ID to each request and response."""

    def __init__(self, get_response: Callable[[HttpRequest], HttpResponse]) -> None:
        self.get_response = get_response

    def __call__(self, request: HttpRequest) -> HttpResponse:
        request_id = request.headers.get("X-Request-ID") or uuid.uuid4().hex
        request.request_id = request_id  # type: ignore[attr-defined]
        response = self.get_response(request)
        response["X-Request-ID"] = request_id
        return response

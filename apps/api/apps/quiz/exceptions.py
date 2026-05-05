"""Wrap DRF exceptions in a consistent error envelope."""
from __future__ import annotations

from typing import Any

from rest_framework.response import Response
from rest_framework.views import exception_handler


def envelope_exception_handler(exc: Exception, context: dict[str, Any]) -> Response | None:
    response = exception_handler(exc, context)
    if response is None:
        return None

    request = context.get("request")
    request_id = getattr(request, "request_id", None) if request is not None else None

    detail = response.data
    code = "error"
    message: str
    if isinstance(detail, dict):
        message = str(detail.get("detail", detail))
        code = str(detail.get("code", code))
    elif isinstance(detail, list):
        message = "; ".join(str(item) for item in detail)
    else:
        message = str(detail)

    retryable = response.status_code >= 500 or response.status_code == 429

    response.data = {
        "code": code,
        "message": message,
        "retryable": retryable,
        "request_id": request_id,
    }
    return response

"""Shared pytest fixtures."""
from __future__ import annotations

import pytest


@pytest.fixture
def api_client():
    from rest_framework.test import APIClient
    return APIClient()

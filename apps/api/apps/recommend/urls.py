"""Admin URL patterns for the A/B variant harness."""
from __future__ import annotations

from django.urls import path

from .views import VariantCompareView, VariantListCreateView, VariantResultsView

app_name = "recommend"

urlpatterns = [
    path("variants", VariantListCreateView.as_view(), name="variants"),
    path("variants/compare", VariantCompareView.as_view(), name="variants-compare"),
    path(
        "variants/<int:variant_id>/results",
        VariantResultsView.as_view(),
        name="variant-results",
    ),
]

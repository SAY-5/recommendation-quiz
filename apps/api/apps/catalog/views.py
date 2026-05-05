"""Catalog endpoints."""
from __future__ import annotations

from drf_spectacular.utils import extend_schema
from rest_framework import generics

from .models import Product
from .serializers import ProductDetailSerializer


@extend_schema(responses={200: ProductDetailSerializer})
class ProductDetailView(generics.RetrieveAPIView):  # type: ignore[type-arg]
    queryset = Product.objects.prefetch_related("attributes").all()
    serializer_class = ProductDetailSerializer
    lookup_field = "id"

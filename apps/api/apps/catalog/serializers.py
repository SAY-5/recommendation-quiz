"""Catalog serializers."""
from __future__ import annotations

from rest_framework import serializers

from .models import Product, ProductAttribute


class ProductAttributeSerializer(serializers.ModelSerializer[ProductAttribute]):
    class Meta:
        model = ProductAttribute
        fields = ("key", "value")


class ProductDetailSerializer(serializers.ModelSerializer[Product]):
    attributes = ProductAttributeSerializer(many=True, read_only=True)

    class Meta:
        model = Product
        fields = ("id", "name", "brand", "price_cents", "image_url", "attributes")

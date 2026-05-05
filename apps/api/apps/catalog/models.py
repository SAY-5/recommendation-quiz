"""Catalog domain models: Product and ProductAttribute."""
from __future__ import annotations

from django.db import models


class AttributeKey(models.TextChoices):
    ROAST_LEVEL = "roast_level", "Roast level"
    FLAVOR_PROFILE = "flavor_profile", "Flavor profile"
    CAFFEINE_MG = "caffeine_mg", "Caffeine (mg per serving)"
    BREW_METHOD_COMPATIBILITY = "brew_method_compatibility", "Brew method compatibility"
    PRICE_TIER = "price_tier", "Price tier (1=budget, 5=premium)"
    MILK_FRIENDLY = "milk_friendly", "Milk-friendly"
    ACIDITY = "acidity", "Acidity (1=low, 5=bright)"


class Product(models.Model):
    name = models.CharField(max_length=128)
    brand = models.CharField(max_length=64)
    price_cents = models.PositiveIntegerField()
    image_url = models.URLField(blank=True, default="")

    class Meta:
        ordering = ["brand", "name"]

    def __str__(self) -> str:
        return f"{self.brand} — {self.name}"


class ProductAttribute(models.Model):
    """Key-value attribute for a product. ``value`` is JSON: scalar, list, or {min,max}."""

    product = models.ForeignKey(
        Product,
        on_delete=models.CASCADE,
        related_name="attributes",
    )
    key = models.CharField(max_length=64, choices=AttributeKey.choices)
    value = models.JSONField()

    class Meta:
        ordering = ["product_id", "key"]
        constraints = [
            models.UniqueConstraint(
                fields=["product", "key"],
                name="unique_attribute_per_product",
            ),
        ]

    def __str__(self) -> str:
        return f"{self.product_id}:{self.key}={self.value!r}"

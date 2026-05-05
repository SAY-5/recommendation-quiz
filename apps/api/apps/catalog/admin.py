from django.contrib import admin

from .models import Product, ProductAttribute


class ProductAttributeInline(admin.TabularInline):  # type: ignore[type-arg]
    model = ProductAttribute
    extra = 0


@admin.register(Product)
class ProductAdmin(admin.ModelAdmin):  # type: ignore[type-arg]
    list_display = ("brand", "name", "price_cents")
    search_fields = ("brand", "name")
    inlines = [ProductAttributeInline]

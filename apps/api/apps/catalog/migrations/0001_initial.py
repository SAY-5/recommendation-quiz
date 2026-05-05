from django.db import migrations, models


class Migration(migrations.Migration):
    initial = True

    dependencies = []

    operations = [
        migrations.CreateModel(
            name="Product",
            fields=[
                (
                    "id",
                    models.BigAutoField(
                        auto_created=True,
                        primary_key=True,
                        serialize=False,
                        verbose_name="ID",
                    ),
                ),
                ("name", models.CharField(max_length=128)),
                ("brand", models.CharField(max_length=64)),
                ("price_cents", models.PositiveIntegerField()),
                ("image_url", models.URLField(blank=True, default="")),
            ],
            options={"ordering": ["brand", "name"]},
        ),
        migrations.CreateModel(
            name="ProductAttribute",
            fields=[
                (
                    "id",
                    models.BigAutoField(
                        auto_created=True,
                        primary_key=True,
                        serialize=False,
                        verbose_name="ID",
                    ),
                ),
                (
                    "key",
                    models.CharField(
                        choices=[
                            ("roast_level", "Roast level"),
                            ("flavor_profile", "Flavor profile"),
                            ("caffeine_mg", "Caffeine (mg per serving)"),
                            (
                                "brew_method_compatibility",
                                "Brew method compatibility",
                            ),
                            (
                                "price_tier",
                                "Price tier (1=budget, 5=premium)",
                            ),
                            ("milk_friendly", "Milk-friendly"),
                            ("acidity", "Acidity (1=low, 5=bright)"),
                        ],
                        max_length=64,
                    ),
                ),
                ("value", models.JSONField()),
                (
                    "product",
                    models.ForeignKey(
                        on_delete=models.deletion.CASCADE,
                        related_name="attributes",
                        to="catalog.product",
                    ),
                ),
            ],
            options={"ordering": ["product_id", "key"]},
        ),
        migrations.AddConstraint(
            model_name="productattribute",
            constraint=models.UniqueConstraint(
                fields=("product", "key"),
                name="unique_attribute_per_product",
            ),
        ),
    ]

from django.db import migrations, models


class Migration(migrations.Migration):
    initial = True

    dependencies = []

    operations = [
        migrations.CreateModel(
            name="Question",
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
                ("slug", models.SlugField(max_length=64, unique=True)),
                ("prompt", models.CharField(max_length=255)),
                ("order", models.PositiveIntegerField(default=0)),
                (
                    "kind",
                    models.CharField(
                        choices=[
                            ("single", "Single choice"),
                            ("multi", "Multi choice"),
                            ("range", "Range / ordinal"),
                        ],
                        default="single",
                        max_length=16,
                    ),
                ),
            ],
            options={"ordering": ["order", "id"]},
        ),
        migrations.CreateModel(
            name="AnswerOption",
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
                ("value", models.CharField(max_length=64)),
                ("label", models.CharField(max_length=128)),
                ("order", models.PositiveIntegerField(default=0)),
                (
                    "question",
                    models.ForeignKey(
                        on_delete=models.deletion.CASCADE,
                        related_name="options",
                        to="quiz.question",
                    ),
                ),
            ],
            options={"ordering": ["order", "id"]},
        ),
        migrations.AddConstraint(
            model_name="answeroption",
            constraint=models.UniqueConstraint(
                fields=("question", "value"),
                name="unique_option_value_per_question",
            ),
        ),
    ]

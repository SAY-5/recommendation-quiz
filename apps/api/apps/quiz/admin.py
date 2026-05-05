from django.contrib import admin

from .models import AnswerOption, Question


class AnswerOptionInline(admin.TabularInline):  # type: ignore[type-arg]
    model = AnswerOption
    extra = 0


@admin.register(Question)
class QuestionAdmin(admin.ModelAdmin):  # type: ignore[type-arg]
    list_display = ("order", "slug", "prompt", "kind")
    list_display_links = ("slug",)
    ordering = ("order",)
    inlines = [AnswerOptionInline]

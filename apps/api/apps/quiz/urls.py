from django.urls import path

from .views import QuestionListView, ScoreView

app_name = "quiz"

urlpatterns = [
    path("questions", QuestionListView.as_view(), name="questions"),
    path("score", ScoreView.as_view(), name="score"),
]

from django.urls import path

from .views import ProductDetailView

app_name = "catalog"

urlpatterns = [
    path("<int:id>", ProductDetailView.as_view(), name="product-detail"),
]

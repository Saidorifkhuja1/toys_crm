from django.urls import path
from rest_framework.routers import DefaultRouter

from sales.views import (
    ProductSoldAPIView,
    SaleViewSet,
    MerchantSelfIncomeOverview,
    AdminMerchantIncomeOverview,
)

router = DefaultRouter()
router.register(r"", SaleViewSet, basename="sale")

urlpatterns = [
    path(
        "merchant-sale-income/<uuid:merchant_id>/",
        AdminMerchantIncomeOverview.as_view(),
        name="admin-merchant-income",
    ),
    path(
        "my-income/", MerchantSelfIncomeOverview.as_view(), name="merchant-self-income"
    ),
    path("product-sold/", ProductSoldAPIView.as_view()),
]

urlpatterns += router.urls

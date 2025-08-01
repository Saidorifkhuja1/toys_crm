from django.urls import path
from .views import (
    DashboardCountsView,
    LowStockProductsAPIView,
    MerchantDebtTotalView,
    OutOfStockProductsAPIView,
    ProductBatchTotalSellPriceView,
    SaleDebtTotalView,
    TopSellingProductsAPIView,
    TotalMoneyEarnedView,
)

urlpatterns = [
    path("counts/", DashboardCountsView.as_view(), name="dashboard-counts"),
    path("sale-debts/total/", SaleDebtTotalView.as_view(), name="sale-debt-total"),
    path("asset-value/", ProductBatchTotalSellPriceView.as_view(), name="asset_value"),
    path("income/", TotalMoneyEarnedView.as_view(), name="total-money-earned"),
    path(
        "products/low-stock/",
        LowStockProductsAPIView.as_view(),
        name="low-stock-products",
    ),
    path(
        "products/out-of-stock/",
        OutOfStockProductsAPIView.as_view(),
        name="out-of-stock-products",
    ),
    path(
        "products/top-selling/",
        TopSellingProductsAPIView.as_view(),
        name="top-selling-products",
    ),
    path(
        "merchant-debts/total/",
        MerchantDebtTotalView.as_view(),
        name="merchant-debt-total",
    ),
]

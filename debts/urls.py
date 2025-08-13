from django.urls import path, include
from rest_framework.routers import DefaultRouter

from debts.views import (
    DebtorViewSet,
    MerchantProductDebtDetailAPIView,
    MerchantProductDebtListAPIView,
    SaleDebtViewSet,
    pay_debt,
    PayMerchantDebtAPIView, SendDebtorMessagesView,
)

router = DefaultRouter()
router.register(r"debts", SaleDebtViewSet, basename="sale-debt")
router.register(r"debtors", DebtorViewSet, basename="debtor")

urlpatterns = [
    # SaleDebt and Debtor viewsets
    path("", include(router.urls)),
    # Endpoints to pay debts
    path("pay-debt/", pay_debt, name="pay-debt"),
    path("pay-merchant-debt/<int:product_batch_id>/",PayMerchantDebtAPIView.as_view(),name="pay-merchant-debt",),
    # New: list all debts for the authenticated merchant
    path("merchant-debts/overview/<int:supplier_id>/",MerchantProductDebtListAPIView.as_view(),name="merchant-debt-list",),
    path("merchant-debts/detail/<int:product_id>/",MerchantProductDebtDetailAPIView.as_view(),),
path("debtors/send-messages/", SendDebtorMessagesView.as_view(), name="send-debtor-messages"),
]

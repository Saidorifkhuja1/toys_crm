from rest_framework import generics, permissions
from rest_framework.response import Response
from django.db.models import Sum, DecimalField, F, Count, Value
from django.db.models.functions import Coalesce
from django_filters.rest_framework import DjangoFilterBackend

from core.pagination import GlobalPagination
from .serializers import (
    LowStockProductSerializer,
    OutOfStockProductSerializer,
    TopSellingProductSerializer,
)
from analytics.filterset import IncomeFilter, MerchantDebtFilter, SaleDebtFilter
from core.enums import UserRole
from debts.models import MerchantDebt, SaleDebt
from .serializers import (
    DashboardCountsSerializer,
    AssetValueSerializer,
    TotalSerializer,
)
from products.models import Product, ProductBatch, Category
from members.models import Supplier, User
from sales.models import Sale


class DashboardCountsView(generics.GenericAPIView):
    permission_classes = [permissions.IsAuthenticated]
    serializer_class = DashboardCountsSerializer

    def get(self, request, *args, **kwargs):
        data = {
            "product_count": Product.objects.filter(deleted=False).count(),
            "product_batch_count": ProductBatch.objects.count(),
            "supplier_count": Supplier.objects.filter(deleted=False).count(),
            "merchant_count": User.objects.filter(
                user_role=UserRole.MERCHANT, is_active=True
            ).count(),
            "admin_count": User.objects.filter(
                user_role=UserRole.ADMIN, is_active=True
            ).count(),
            "category_count": Category.objects.filter(deleted=False).count(),
            "sale_count": Sale.objects.count(),
        }
        serializer = self.get_serializer(data=data)
        serializer.is_valid(raise_exception=True)
        return Response(serializer.data)


class SaleDebtTotalView(generics.GenericAPIView):
    """
    Returns the total of all sale‐debt entries (deleted=False),
    filtered by created_at date params and aggregated.
    """

    permission_classes = [permissions.IsAuthenticated]
    serializer_class = TotalSerializer
    filterset_class = SaleDebtFilter

    def get_queryset(self):
        return SaleDebt.objects.filter(deleted=False)

    def get(self, request, *args, **kwargs):
        qs = self.filter_queryset(self.get_queryset())
        total = qs.aggregate(total=Sum("amount"))["total"] or 0
        serializer = self.get_serializer(data={"total": total})
        serializer.is_valid(raise_exception=True)
        return Response(serializer.data)

    def get(self, request, *args, **kwargs):
        qs = self.filter_queryset(self.get_queryset())
        total = qs.aggregate(total=Sum("amount"))["total"] or 0
        serializer = self.get_serializer(data={"total": total})
        serializer.is_valid(raise_exception=True)
        return Response(serializer.data)


class MerchantDebtTotalView(generics.GenericAPIView):
    """
    Returns the aggregate outstanding merchant debt:
    sum(initial_amount - paid_amount) across all non-deleted MerchantDebt,
    filtered by created_at via MerchantDebtFilter.
    """

    permission_classes = [permissions.IsAuthenticated]
    serializer_class = TotalSerializer
    filterset_class = MerchantDebtFilter

    def get_queryset(self):
        return MerchantDebt.objects.filter(deleted=False)

    def get(self, request, *args, **kwargs):
        qs = self.filter_queryset(self.get_queryset())
        total = (
            qs.aggregate(
                total=Sum(
                    F("initial_amount") - F("paid_amount"),
                    output_field=DecimalField(max_digits=20, decimal_places=2),
                )
            )["total"]
            or 0
        )
        serializer = self.get_serializer(data={"total": total})
        serializer.is_valid(raise_exception=True)
        return Response(serializer.data)


class ProductBatchTotalSellPriceView(generics.GenericAPIView):
    permission_classes = [permissions.IsAuthenticated]
    serializer_class = AssetValueSerializer

    def get(self, request, *args, **kwargs):
        total = (
            ProductBatch.objects.annotate(
                total_price=F("quantity") * F("sell_price")
            ).aggregate(total=Sum("total_price"))["total"]
            or 0
        )
        serializer = self.get_serializer({"total": total})
        return Response(serializer.data)


class TotalMoneyEarnedView(generics.GenericAPIView):
    """
    Returns the total amount from sales.
    If ?pure=true -> sum of total_paid
    If ?pure=false or not given -> sum of total_sold
    """

    permission_classes = [permissions.IsAuthenticated]
    serializer_class = TotalSerializer
    filter_backends = [DjangoFilterBackend]
    filterset_class = IncomeFilter
    queryset = Sale.objects.filter(deleted=False)

    def get(self, request, *args, **kwargs):
        pure_param = request.query_params.get("pure", "false").lower()
        pure = pure_param in ("1", "true", "yes")

        field_to_sum = "total_paid" if pure else "total_sold"

        total = (
            self.filter_queryset(self.get_queryset())
            .filter(deleted=False)
            .aggregate(total=Sum(field_to_sum))["total"]
            or 0
        )

        serializer = self.get_serializer(data={"total": total})
        serializer.is_valid(raise_exception=True)
        return Response(serializer.data)


class LowStockProductsAPIView(generics.ListAPIView):
    """
    GET /api/products/low-stock/
    Returns products whose total stock across all batches is less than 50,
    ordered ascending by total stock. Paginated.
    Response format:
    [
      { "id": ..., "name": ..., "count": ... },
      ...
    ]
    """

    serializer_class = LowStockProductSerializer
    pagination_class = GlobalPagination

    def get_queryset(self):
        return (
            Product.objects.annotate(
                count=Coalesce(Sum("product_batches__quantity"), Value(0))
            )
            .filter(count__lt=50)
            .order_by("count")
        )


class OutOfStockProductsAPIView(generics.ListAPIView):
    """
    GET /api/products/out-of-stock/
    Returns products which are fully out of stock (total batch quantity = 0).
    Paginated.
    Response format:
    [
      { "id": ..., "name": ... },
      ...
    ]
    """

    serializer_class = OutOfStockProductSerializer
    pagination_class = GlobalPagination

    def get_queryset(self):
        return (
            Product.objects.annotate(
                count=Coalesce(Sum("product_batches__quantity"), Value(0))
            )
            .filter(count=0)
            .order_by("name")
        )


class TopSellingProductsAPIView(generics.ListAPIView):
    """
    GET /api/products/top-selling/
    Returns top 10 best-selling products, by number of sale items.
    Not paginated (fixed to 10).
    Response format:
    [
      { "id": ..., "name": ..., "sale_count": ... },
      ...
    ]
    """

    serializer_class = TopSellingProductSerializer
    pagination_class = None

    def get_queryset(self):
        return (
            Product.objects.annotate(sale_count=Count("saleitem"))
            .order_by("-sale_count")
            .filter(sale_count__gt=0)[:10]
        )

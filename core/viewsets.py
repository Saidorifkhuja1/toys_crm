from rest_framework.permissions import IsAuthenticated, AllowAny
from rest_framework.response import Response
from drf_yasg.utils import swagger_auto_schema
from drf_yasg import openapi
from rest_framework import viewsets
from rest_framework.exceptions import ValidationError
from rest_framework.generics import GenericAPIView
from datetime import datetime
from django.db.models import Sum, Count, Prefetch

from core.pagination import GlobalPagination
from members.serializers import UserSerializer
from sales.models import Sale, SaleItem, Payment
from sales.serializers import SaleSerializer


class CoreViewSet(viewsets.ModelViewSet):
    """
    Custom base viewset which allows unauthenticated GET access,
    but restricts other methods.
    """

    permission_classes = [IsAuthenticated]
    pagination_class = GlobalPagination

    @swagger_auto_schema(
        manual_parameters=[
            openapi.Parameter(
                "page", openapi.IN_QUERY, type=openapi.TYPE_INTEGER, default=1
            )
        ]
    )
    def get_queryset(self):
        return super().get_queryset().filter(deleted=False)

    def perform_create(self, serializer):
        serializer.save(created_by=self.request.user)

    def perform_update(self, serializer):
        return serializer.save(updated_by=self.request.user)

    @swagger_auto_schema(auto_schema=None)
    def update(self, request, *args, **kwargs):
        # Disable PUT
        return super().update(request, *args, **kwargs)

    def perform_destroy(self, instance):
        instance.deleted = True
        instance.save()


class CoreReadOnlyViewSet(viewsets.ReadOnlyModelViewSet):
    """
    Custom base viewset which allows unauthenticated GET access,
    but restricts other methods.
    """

    @swagger_auto_schema(
        manual_parameters=[
            openapi.Parameter(
                "page", openapi.IN_QUERY, type=openapi.TYPE_INTEGER, default=1
            )
        ]
    )
    def list(self, request, *args, **kwargs):
        return super().list(request, *args, **kwargs)

    permission_classes = [AllowAny]
    pagination_class = GlobalPagination


class BaseProductViewSet(CoreViewSet):
    def get_permissions(self):
        if self.action in ["list", "retrieve", "options"]:
            return []
        return super().get_permissions()


class UpdateMessageMixin:
    def post(self, request, *args, **kwargs):
        response = super().post(request, *args, **kwargs)
        response.data["message"] = "Tizimga kirish muvaffaqiyatli amalga oshirildi"
        return response


class BaseMerchantIncomeOverview(GenericAPIView):
    permission_classes = [IsAuthenticated]
    pagination_class = GlobalPagination

    def get_target_date(self):
        date_str = self.request.query_params.get("date")
        return datetime.strptime(date_str, "%Y-%m-%d").date() if date_str else None

    def get_date_range(self):
        start_date_str = self.request.query_params.get("start_date")
        end_date_str = self.request.query_params.get("end_date")

        if start_date_str and end_date_str:
            try:
                start_date = datetime.strptime(start_date_str, "%Y-%m-%d").date()
                end_date = datetime.strptime(end_date_str, "%Y-%m-%d").date()
                if start_date > end_date:
                    start_date, end_date = end_date, start_date
                return {"start_date": start_date, "end_date": end_date}
            except ValueError:
                raise ValidationError("Invalid date format in start_date or end_date.")

        return None

    def validate_date_inputs(self):
        if self.get_target_date() and self.get_date_range():
            raise ValidationError("Cannot use both single date and date range.")

    def get_sales_queryset(self, merchant):
        deleted = self.request.query_params.get("deleted", False)
        self.validate_date_inputs()

        queryset = (
            Sale.objects.filter(
                merchant=merchant, deleted=deleted in ["true", "1", "yes"]
            )
            .select_related("merchant", "debtor")
            .prefetch_related(
                Prefetch(
                    "items",
                    queryset=SaleItem.objects.select_related(
                        "product__category", "product__supplier"
                    ).prefetch_related("product__product_batches"),
                ),
                Prefetch(
                    "payment__payments",
                    queryset=Payment.objects.select_related("sale_payment"),
                ),
            )
        )

        date_range = self.get_date_range()
        target_date = self.get_target_date()

        if date_range:
            queryset = queryset.filter(
                created_at__date__gte=date_range["start_date"],
                created_at__date__lte=date_range["end_date"],
            )
        elif target_date:
            queryset = queryset.filter(created_at__date=target_date)

        print(queryset)
        return queryset

    def calculate_totals(self, merchant_id):
        self.validate_date_inputs()

        date_range = self.get_date_range()
        target_date = self.get_target_date()

        queryset = Sale.objects.filter(merchant_id=merchant_id, deleted=False)

        if date_range:
            queryset = queryset.filter(
                created_at__date__gte=date_range["start_date"],
                created_at__date__lte=date_range["end_date"],
            )
        elif target_date:
            queryset = queryset.filter(created_at__date=target_date)

        totals = queryset.aggregate(
            total_income=Sum("total_paid"), total_sales=Count("id")
        )
        item_totals = SaleItem.objects.filter(
            sale__in=queryset, deleted=False
        ).aggregate(
            unique_products=Count("product", distinct=True),
            total_quantity=Sum("quantity"),
        )

        return {
            "income": int(totals["total_income"] or 0),
            "sales": int(totals["total_sales"] or 0),
            "products": int(item_totals["unique_products"] or 0),
            "quantity": int(item_totals["total_quantity"] or 0),
        }

    def format_period_data(self):
        date_range = self.get_date_range()
        target_date = self.get_target_date()
        if date_range:
            return {
                "start_date": date_range["start_date"].isoformat(),
                "end_date": date_range["end_date"].isoformat(),
                "is_single_day": False,
            }
        elif target_date:
            return {
                "start_date": target_date.isoformat(),
                "end_date": target_date.isoformat(),
                "is_single_day": True,
            }
        return {}

    def build_response(self, queryset, merchant):
        # 1. Paginate the queryset
        page = self.paginate_queryset(queryset.order_by("-created_at"))
        # 2. Serialize only the objects on this page
        serialized_sales = SaleSerializer(page, many=True).data
        # 3. Grab the built-in paginated response (count, total_pages, results)
        paginated_data = self.paginator.get_paginated_response(serialized_sales).data

        # 4. Merge your merchant/totals/period into that pagination envelope
        return Response(
            {
                "merchant": UserSerializer(merchant).data,
                "totals": self.calculate_totals(merchant.id),
                "period": self.format_period_data(),
                "count": paginated_data["count"],
                "total_pages": paginated_data["total_pages"],
                "results": paginated_data["results"],
            }
        )

from rest_framework.decorators import permission_classes
from rest_framework import status
from django.db import transaction
from django.db.models import Exists, OuterRef
from rest_framework.permissions import IsAuthenticated, AllowAny
from rest_framework.decorators import api_view
from rest_framework.response import Response
from rest_framework.generics import CreateAPIView, DestroyAPIView
from rest_framework.exceptions import ValidationError

from core.mixins import InventoryLoggingMixin, PaymentMixin
from debts.models import MerchantDebt
from logs.models import BatchLog, ProductLog
from products.filters import ProductFilter
from products.utils import remove_product_image
from sales.models import Sale
from sales.serializers import EmptySerializer
from .serializers import (
    ProductForSaleSerializer,
    ProductBatchSerializer,
    CategorySerializer,
    ProductSerializer,
    MediaSerializer,
)
from core.viewsets import BaseProductViewSet, CoreReadOnlyViewSet, CoreViewSet
from sales.utils import calculate_monthly_income, after_product_prices
from products.models import Category, Product, ProductBatch, ProductPayments
from products.pagination import ProductForSalePagination


class ProductViewSet(PaymentMixin, InventoryLoggingMixin, BaseProductViewSet):
    queryset = Product.objects.all().order_by("-created_at")
    serializer_class = ProductSerializer
    search_fields = ["name", "sku"]
    filterset_class = ProductFilter

    lookup_field = "sku"
    lookup_url_kwarg = "sku"
    # configuration for the mixin
    log_model = ProductLog
    log_fk_field = "product"
    create_note_template = "{instance.name} nomli mahsulot qo'shildi"
    update_note_template = "{instance.name} nomli mahsulotning quyidagi ma'lumotlari o'zgartirildi: {changes}"
    delete_note_template = "{instance.sku} SKUli mahsulot o'chirildi"

    @transaction.atomic
    def create(self, request, supplier_id, *args, **kwargs):
        user = request.user
        serializer = self.get_serializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        if supplier_id is None:
            raise ValidationError("Supplier id not provided")

        validated_data = serializer.validated_data
        batch_data = validated_data.pop("product_batch")
        payment_data = batch_data.pop("payment")

        # Create product
        product = Product.objects.create(supplier_id=supplier_id, **validated_data)

        # Create product batch
        product_batch = ProductBatch.objects.create(
            product=product, created_by=user, **batch_data
        )
        self.product_batch = product_batch
        # Use shared utility for collecting payments
        payments, paid_amount = self.collect_payments(user=user, payment=payment_data)

        # Calculate initial amount and merchant debt
        initial = product_batch.buy_price * product_batch.quantity
        if paid_amount > initial:
            raise ValidationError("Overpayment is not allowed.")
        elif paid_amount < initial:
            MerchantDebt.objects.create(
                merchant=user,
                product_batch=product_batch,
                initial_amount=initial,
                paid_amount=paid_amount,
                created_by=user,
            )
        ProductPayments.objects.bulk_create(payments)
        return Response({"id": product.id}, status=status.HTTP_201_CREATED)

    def get_queryset(self):
        supplier_id, deleted = self.kwargs.get("supplier_id", None), self.kwargs.get(
            "supplier_id", False
        )
        deleted = deleted in ["yes", "true", "1"]
        if supplier_id is not None:
            return (
                super().get_queryset().filter(supplier_id=supplier_id, deleted=deleted)
            )
        return super().get_queryset()

    def perform_destroy(self, instance):
        merchant_debts = MerchantDebt.objects.filter(
            product_batch__product__id=instance.id, deleted=False
        ).exists()
        batches = ProductBatch.objects.filter(
            product_id=instance.id, deleted=False
        ).exists()
        if merchant_debts:
            raise ValidationError("Bu mahsulotni qarzi bor")
        elif batches:
            raise ValidationError("Omborda bu mahsulotni partiyalari mavjud!")
        return super().perform_destroy(instance)


class ProductBatchViewSet(BaseProductViewSet, InventoryLoggingMixin, PaymentMixin):
    queryset = ProductBatch.objects.filter(deleted=False).order_by("-created_at")
    serializer_class = ProductBatchSerializer
    search_fields = ["name"]

    log_model = BatchLog
    log_fk_field = "batch"
    create_note_template = (
        "{instance.product.name} ning yangi partiyasi qo'shildi (ID={instance.id})"
    )
    update_note_template = "{instance.product.name} ning partiyasi (ID={instance.id}) ma'lumotlari o'zgartirildi: {changes}"
    delete_note_template = (
        "{instance.product.name} ning partiyasi (ID={instance.id}) o'chirildi"
    )

    def get_queryset(self):
        qs = super().get_queryset()
        product_id = self.request.query_params.get("product_id")
        if product_id:
            qs = qs.filter(product_id=product_id)
        return qs

    @transaction.atomic
    def create(self, request, *args, **kwargs):
        payment = request.data.pop("payment", None)
        response = super().create(request, *args, **kwargs)
        try:
            product_batch = ProductBatch.objects.get(id=response.data["id"])
        except ProductBatch.DoesNotExist:
            raise ValidationError(
                "Product batch not found, likely due to failure in product batch creation"
            )
        self.product_batch = product_batch
        if payment is not None:
            payments, paid_amount = self.collect_payments(payment, request.user)
            initial = product_batch.buy_price * product_batch.quantity

            if paid_amount > initial:
                raise ValidationError("Overpayment is not allowed.")

            MerchantDebt.objects.create(
                merchant=request.user,
                product_batch=product_batch,
                initial_amount=initial,
                paid_amount=paid_amount,
                created_by=request.user,
            )

            ProductPayments.objects.bulk_create(payments)

        return response

    def perform_destroy(self, instance):
        if MerchantDebt.objects.filter(
            product_batch_id=instance.id, deleted=False
        ).exists():
            raise ValidationError("Bu partiyada qarz mavjud")
        return super().perform_destroy(instance)


class ProductForSaleViewSet(CoreReadOnlyViewSet):
    queryset = Product.objects.order_by("-created_at").filter(deleted=False)
    serializer_class = ProductForSaleSerializer
    pagination_class = ProductForSalePagination
    search_fields = ["name"]

    def get_queryset(self):
        # Subquery: check if ProductBatch exists with quantity > 0 for each Product
        has_available_batch = ProductBatch.objects.filter(
            product=OuterRef("pk"), quantity__gt=0, deleted=False
        )

        return (
            Product.objects.annotate(has_available=Exists(has_available_batch))
            .filter(deleted=False, has_available=True)
            .order_by("-created_at")
        )


class CategoryViewSet(CoreViewSet):
    def get_permissions(self):
        if self.request.method in ["POST", "PUT", "PATCH", "DELETE"]:
            return super().get_permissions()
        else:
            return [AllowAny()]

    queryset = Category.objects.filter(deleted=False).order_by("-created_at")
    serializer_class = CategorySerializer


class MediaCreateView(CreateAPIView):
    serializer_class = MediaSerializer
    queryset = Product.objects.filter(deleted=False).order_by("-created_at")

    def create(self, request, *args, **kwargs):
        image = request.FILES.get("image")
        product_id = request.data.get("product_id")

        if not image or not product_id:
            return Response({"error": "Image and product_id are required"}, status=400)

        try:
            product = Product.objects.get(id=product_id)

            try:
                remove_product_image(product)
            except FileNotFoundError:
                pass

            product.image = image
            product.save()

            return Response({"message": "Image uploaded successfully"}, status=201)

        except Product.DoesNotExist:
            return Response({"error": "Product not found"}, status=404)
        except Exception as e:
            return Response({"error": str(e)}, status=500)


class MediaDeleteView(DestroyAPIView):
    serializer_class = EmptySerializer
    queryset = Product.objects.none()  # Swagger uchun kerak

    def destroy(self, request, *args, **kwargs):
        if getattr(self, 'swagger_fake_view', False):
            return Response(status=status.HTTP_200_OK)  # Swagger uchun short-circuit

        try:
            product = Product.objects.get(id=kwargs.get("pk"))

            try:
                remove_product_image(product)
            except FileNotFoundError as e:
                return Response({"error": str(e)}, status=404)

            product.image = None
            product.save()

            return Response(status=204)

        except Product.DoesNotExist:
            return Response({"error": "Product not found"}, status=404)
        except Exception as e:
            return Response({"error": str(e)}, status=500)

@api_view(["GET"])
@permission_classes([IsAuthenticated])
def get_count(request):
    """
    Placeholder for get_count function.
    Implement this function when product count retrieval is required.
    """

    income = calculate_monthly_income()
    return Response(
        {
            "products": Product.objects.count(),
            "afterProductPrices": after_product_prices(),
            "income": income,
            "totalSales": Sale.objects.count(),
        }
    )

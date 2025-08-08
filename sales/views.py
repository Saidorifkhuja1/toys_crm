from rest_framework import serializers, status
from rest_framework.response import Response
from django.db import transaction, models
from rest_framework import generics
from django.db.models import Sum, F, Case, When, IntegerField, Value as V
from django.db.models.functions import Coalesce
from rest_framework.generics import ListAPIView

from core.pagination import GlobalPagination
from core.permissions import IsAdminUser
from user.models import User
from sales.models import Payment, Sale, SaleItem, SaleItemBatch, SalePayment
from sales.filters import SaleFilter
from sales.serializers import SaleSerializer, EmptySerializer, PaymentSerializer
from core.viewsets import BaseMerchantIncomeOverview, CoreViewSet
from products.models import ProductBatch, Product
from debts.models import SaleDebt
from core.enums import UserRole


class SaleViewSet(CoreViewSet):
    queryset = Sale.objects.filter(deleted=False).order_by("-created_at")
    serializer_class = SaleSerializer
    filterset_class = SaleFilter

    def get_queryset(self):
        return (
            Sale.objects.select_related("merchant", "debtor")
            .prefetch_related(
                "items__product", "items__batches__product_batch", "payment"
            )
            .order_by("-created_at")
        )

    @transaction.atomic
    def create(self, request, *args, **kwargs):
        sale_data = self.get_serializer(data=request.data)
        sale_data.is_valid(raise_exception=True)
        debtor = sale_data.validated_data.pop("debtor_id", None)
        total_sold = sale_data.validated_data.pop("total_sold")
        items = sale_data.validated_data.pop("items")
        payments = sale_data.validated_data.pop("payment", [])
        exchange_rate = sale_data.validated_data.pop("exchange_rate")

        # create sale record
        sale = Sale.objects.create(
            total_sold=total_sold,
            merchant=request.user,
            debtor=debtor,
            created_by=request.user,
        )

        # subtract inventory using bulk operations
        for item in items:
            sale_item = SaleItem.objects.create(
                sale=sale,
                product=item["product_id"],
                quantity=item["quantity"],
                created_by=request.user,
            )
            remaining = item["quantity"]
            batches = list(
                ProductBatch.objects.filter(
                    product=item["product_id"], quantity__gt=0, deleted=False
                ).order_by("created_at")
            )
            sibs = []
            updated_batches = []

            for batch in batches:
                if remaining <= 0:
                    break
                used = min(batch.quantity, remaining)
                batch.quantity -= used
                remaining -= used

                sibs.append(
                    SaleItemBatch(
                        sale_item=sale_item,
                        product_batch=batch,
                        quantity_used=used,
                    )
                )
                updated_batches.append(batch)

            if remaining > 0:
                raise serializers.ValidationError(
                    {"items": f"Omborda yetarli {item['product_id'].name} mavjud emas"}
                )

            ProductBatch.objects.bulk_update(updated_batches, ["quantity"])
            SaleItemBatch.objects.bulk_create(sibs)

        total_paid = 0
        sale_payment = SalePayment.objects.create(
            sale=sale,
            exchange_rate=exchange_rate,
            created_by=request.user,
            debtor=debtor,
        )

        payment_list = []
        for payment in payments:
            payment_list.append(
                Payment(
                    sale_payment=sale_payment,
                    method=payment["method"],
                    amount=payment["amount"],
                )
            )
            if payment["method"] == "USD" or payment["method"] == "usd":
                if exchange_rate is None:
                    raise serializers.ValidationError(
                        detail="Dollarda savdo qilish uchun dollar kursi kiritilishi kerak"
                    )
                total_paid += payment["amount"] * exchange_rate
            else:
                total_paid += payment["amount"]

        Payment.objects.bulk_create(payment_list)

        debt_amount = total_sold - total_paid
        if total_paid < total_sold:
            if debtor is None:
                raise serializers.ValidationError(
                    {
                        "error": f"Nasiyaga savdo qilish uchun qarzdorni tanlashingiz shart {total_paid}  umumiy sotilgan summa: {total_sold}"
                    }
                )
            # debt_message = f"Assalomu alaykum {debtor.full_name}\n Xaridingiz muvaffaqiyatli amalga oshirildi.\n Sotuvchi: {self.request.user.full_name} Qarz miqdori: {debt_amount} so'm. \nIltimos qarzingizni vaqtida to'lab qo'ying. Xaridingizdan mamnunmiz!"
            # send_sms_async(debtor.phone_number, debt_message)
            SaleDebt.objects.create(
                sale=sale,
                amount=debt_amount,
                initial_amount=debt_amount,
                debtor=debtor,
                created_by=request.user,
            )
            debtor.has_debt = True
            debtor.save()
        elif total_paid > total_sold:
            raise serializers.ValidationError(
                {"error": "Ortiqcha to'lov amalga oshirish mumkin emas"}
            )
        sale.total_paid = total_paid
        sale.save()

        return Response(
            {
                "msg": f"Sotuv muvaffaqiyatli amalga oshirildi",
                "sale": SaleSerializer(sale).data,
            },
            status=status.HTTP_201_CREATED,
        )

    def list(self, request, *args, **kwargs):
        queryset = self.filter_queryset(self.get_queryset())
        page = self.paginate_queryset(queryset)

        # Calculate totals over the entire filtered queryset
        total_sold_price = (
            queryset.aggregate(total=models.Sum("total_sold"))["total"] or 0
        )
        total_paid_price = (
            queryset.aggregate(total=models.Sum("total_paid"))["total"] or 0
        )
        remaining_debt = total_sold_price - total_paid_price

        if page is not None:
            serializer = self.get_serializer(page, many=True)
            response = self.get_paginated_response(serializer.data)
            total = {
                "sold": total_sold_price,
                "paid": total_paid_price,
                "debt": remaining_debt,
            }
            # Add totals to response payload
            response.data["total"] = total
            return response

        # If pagination not applied
        serializer = self.get_serializer(queryset, many=True)
        return Response(serializer.data)


class AdminMerchantIncomeOverview(BaseMerchantIncomeOverview):
    permission_classes = [IsAdminUser]
    serializer_class = EmptySerializer
    def get(self, request, *args, **kwargs):
        merchant_id = self.kwargs.get("merchant_id")

        try:
            merchant = User.objects.get(id=merchant_id)
        except User.DoesNotExist:
            return Response({"error": "Merchant not found"}, status=404)

        queryset = self.get_sales_queryset(merchant)
        return self.build_response(queryset, merchant)


class MerchantSelfIncomeOverview(BaseMerchantIncomeOverview):
    serializer_class = EmptySerializer

    def get(self, request, *args, **kwargs):
        user = request.user
        queryset = self.get_sales_queryset(user)
        return self.build_response(queryset, user)


class ProductSoldAPIView(ListAPIView):
    pagination_class = GlobalPagination
    permission_classes = [IsAdminUser]
    serializer_class = EmptySerializer

    def get_queryset(self):
        return (
            Product.objects.annotate(
                sold=Coalesce(
                    Sum(
                        Case(
                            When(
                                product_batches__saleitembatch__sale_item__sale__payment__payments__method="USD",
                                then=F(
                                    "product_batches__saleitembatch__sale_item__sale__payment__payments__amount"
                                )
                                * F(
                                    "product_batches__saleitembatch__sale_item__sale__payment__exchange_rate"
                                ),
                            ),
                            When(
                                product_batches__saleitembatch__sale_item__sale__payment__payments__method="UZS",
                                then=F(
                                    "product_batches__saleitembatch__sale_item__sale__payment__payments__amount"
                                ),
                            ),
                            output_field=IntegerField(),
                        )
                    ),
                    V(0),
                )
            )
            .distinct()
            .order_by("-created_at")
        )

    def list(self, request, *args, **kwargs):
        queryset = self.paginate_queryset(self.get_queryset())
        data = [
            {"product_name": product.name, "sold": product.sold} for product in queryset
        ]
        return self.get_paginated_response(data)


class PaymentListAPIView(generics.ListAPIView):
    queryset = Payment.objects.all()
    serializer_class = PaymentSerializer
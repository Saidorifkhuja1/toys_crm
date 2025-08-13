from rest_framework.permissions import IsAuthenticated
from rest_framework.generics import GenericAPIView, UpdateAPIView
from rest_framework.response import Response
from django.db import transaction
from django.db.models import Prefetch
from rest_framework.exceptions import ValidationError
from rest_framework.decorators import api_view, permission_classes
from django.db.models import F, IntegerField, Sum, Q, OuterRef, Exists
import requests
from django.conf import settings
from rest_framework import generics, status
from core.mixins import PaymentMixin
from core.pagination import GlobalPagination
from debts.serializers import (
    DebtorSerializer,
    ProductDebtSummarySerializer,
    PayDebtSerializer,
    ProductBatchDetailSerializer,
    SaleDebtSerializer,
)
from debts.models import Debtor, MerchantDebt, SaleDebt
from core.viewsets import CoreReadOnlyViewSet, CoreViewSet
from products.models import Product, ProductBatch, ProductPayments
from sales.models import Payment, Sale, SalePayment
from sales.serializers import EmptySerializer


class SaleDebtViewSet(CoreReadOnlyViewSet):
    queryset = SaleDebt.objects.all().order_by("-created_at")
    serializer_class = SaleDebtSerializer

    def get_queryset(self):
        deleted_param = self.request.query_params.get("deleted", "false").lower()
        deleted = deleted_param in ["1", "true", "yes"]

        qs = super().get_queryset().filter(deleted=deleted)
        try:
            qs = qs.select_related("sale__merchant").prefetch_related(
                "sale__items__product"
            )
        except Exception:
            pass
        debtor_id = self.request.query_params.get("debtor_id")
        if debtor_id:
            qs = qs.filter(debtor_id=debtor_id)
        return qs


class DebtorViewSet(CoreViewSet):
    queryset = Debtor.objects.filter(deleted=False).order_by("-created_at")
    serializer_class = DebtorSerializer
    search_fields = ["full_name", "phone_number"]

    @transaction.atomic
    def create(self, request, *args, **kwargs):
        debt_object = request.data.pop("debt", None)
        debtor_data = self.get_serializer(data=request.data)
        debtor_data.is_valid(raise_exception=True)
        debtor = Debtor.objects.create(**debtor_data.validated_data)
        if debt_object is not None:
            debt_serializer = SaleDebtSerializer(data=debt_object)
            debt_serializer.is_valid(raise_exception=True)
            debt_amount = debt_serializer.validated_data.get("amount", 0)
            if debt_amount > 0:
                SaleDebt.objects.create(
                    amount=debt_amount,
                    initial_amount=debt_amount,
                    debtor=debtor,
                    sale=debt_serializer.validated_data.get("sale", None),
                )
                debtor.has_debt = True
            else:
                debtor.has_debt = False
        debtor.save()
        return Response({"msg": "Qarzdor yaratildi"}, status=201)

    def perform_destroy(self, instance):
        sale_debt = SaleDebt.objects.filter(debtor=instance, deleted=False).first()
        if sale_debt or instance.has_debt:
            raise ValidationError(
                {
                    "error": "Bu qarz oluvchi hali ham qarzga ega, o'chirish mumkin emas!"
                },
                code=400,
            )
        else:
            return super().perform_destroy(instance)


@api_view(["POST"])
@permission_classes([IsAuthenticated])
def pay_debt(request):
    payDebt = PayDebtSerializer(data=request.data)
    payDebt.is_valid(raise_exception=True)
    debt_id = payDebt.validated_data.get("debt_id")
    debtor_id = payDebt.validated_data.get("debtor_id")
    sale_id = payDebt.validated_data["sale_id"]
    payments = payDebt.validated_data["payments"]
    exchange_rate = payDebt.validated_data.get("exchange_rate", None)

    # Get sale and debtor
    total_payment_amount_uzs = 0
    try:
        sale = Sale.objects.get(id=sale_id)
    except Sale.DoesNotExist:
        sale = None
    try:
        if sale is not None:
            sale_debt = SaleDebt.objects.filter(
                sale=sale, debtor=sale.debtor, deleted=False
            ).first()
        else:
            sale_debt = SaleDebt.objects.get(id=debt_id, deleted=False)
    except SaleDebt.DoesNotExist:
        raise ValidationError({"error": "Qarz topilmadi!"}, code=404)

    with transaction.atomic():
        # Calculate total payment amount in UZS (converting USD if needed)
        for payment in payments:
            amount = payment["amount"]
            payment_type = payment["method"]

            if payment_type == "usd":
                # Convert USD to UZS using exchange rate
                uzs_amount = exchange_rate * amount
                total_payment_amount_uzs += uzs_amount
            else:
                # UZS and Card payments are already in UZS
                total_payment_amount_uzs += amount

        try:
            debtor = Debtor.objects.get(id=debtor_id)
        except Debtor.DoesNotExist:
            raise ValidationError("Qarzdor topilmadi")

        # Check if total payment (in UZS) exceeds debt
        if total_payment_amount_uzs > sale_debt.amount:
            return Response(
                {"error": "Kiritilgan to'lov miqdori qarz miqdoridan oshib ketdi!"},
                status=400,
            )

        # Update sale debt
        if total_payment_amount_uzs < sale_debt.amount:
            print("total_payment_amount_uzs < sale_debt.amount")
            sale_debt.amount -= total_payment_amount_uzs
            sale_debt.save()
        elif total_payment_amount_uzs == sale_debt.amount:
            print("total_payment_amount_uzs == sale_debt.amount")
            sale_debt.amount = 0
            sale_debt.deleted = True
            debtor.has_debt = False
            debtor.save()
            sale_debt.save()

        if sale is not None:
            sale.total_paid += total_payment_amount_uzs
            sale.save()
        # Create SalePayment
        sale_payment = SalePayment.objects.create(
            sale=sale,
            created_by=request.user,
            exchange_rate=exchange_rate,
            debtor=debtor,
        )

        # Create individual Payment records
        payment_objects = []
        for payment_data in payments:
            payment = Payment(
                sale_payment=sale_payment,
                method=payment_data["method"],
                amount=payment_data["amount"],
            )
            payment_objects.append(payment)
        Payment.objects.bulk_create(payment_objects)
    # send_sms_async(
    #     sale.debtor.phone_number,
    #     f"Assalomu alaykum {sale.debtor.full_name}, Qarzingiz to'landi. To'lov miqdori: {total_payment_amount_uzs}, Qolgan qarz: {sale_debt.amount - total_payment_amount_uzs}",
    # )
    return Response(
        {
            "message": "Qarz muvaffaqiyatli to'landi",
            "sale_payment_id": sale_payment.id,
            "total_amount_uzs": total_payment_amount_uzs,
            "exchange_rate": exchange_rate,
        },
        status=200,
    )


class PayMerchantDebtAPIView(PaymentMixin, UpdateAPIView):

    """
    POST /merchant-debts/{product_batch_id}/pay/
    Body: { exchange_rate: int, payments: [{ method, amount }, …] }
    Applies a payment to an existing MerchantDebt; raises 400 on overpayment.
    """

    queryset = MerchantDebt.objects.all()
    permission_classes = [IsAuthenticated]
    serializer_class = EmptySerializer
    http_method_names = ["post"]
    lookup_url_kwarg = "product_batch_id"

    @transaction.atomic
    def post(self, request, *args, **kwargs):
        batch_id = self.kwargs.get(self.lookup_url_kwarg)
        if not batch_id:
            raise ValidationError({"detail": "Product batch id not provided."})

        try:
            debt = MerchantDebt.objects.get(product_batch_id=batch_id)
        except MerchantDebt.DoesNotExist:
            raise ValidationError({"detail": "Qarz topilmadi"})

        # set for mixin
        self.product_batch = debt.product_batch
        payment = request.data.pop("payment", None)
        if payment is None:
            raise ValidationError("Payment object not provided")
        payments, paid_amount = self.collect_payments(payment, request.user)

        new_paid = debt.paid_amount + paid_amount
        if new_paid > debt.initial_amount:
            raise ValidationError({"detail": "Ko'p pul to'lab yubordingiz!"})

        # save payments and update debt
        ProductPayments.objects.bulk_create(payments)
        if new_paid == debt.initial_amount:
            debt.deleted = True
        debt.paid_amount = new_paid
        debt.save(update_fields=["paid_amount", "deleted"])

        return Response(
            {
                "message": "To'lov amalga oshirildi!",
                "paid_amount": debt.paid_amount,
            },
            status=status.HTTP_200_OK,
        )


class MerchantProductDebtListAPIView(GenericAPIView):
    permission_classes = [IsAuthenticated]
    serializer_class = ProductDebtSummarySerializer
    pagination_class = GlobalPagination

    def get(self, request, supplier_id, *args, **kwargs):
        deleted_param = request.query_params.get("deleted", "false").lower()
        deleted = deleted_param in ["1", "true", "yes"]

        # Subqueries
        has_undeleted = MerchantDebt.objects.filter(
            product_batch__product=OuterRef("pk"), deleted=False
        )
        has_any_debt = MerchantDebt.objects.filter(
            product_batch__product=OuterRef("pk")
        )

        base_qs = Product.objects.filter(supplier_id=supplier_id)

        if deleted:
            qs = base_qs.annotate(
                has_undeleted=Exists(has_undeleted), has_any_debt=Exists(has_any_debt)
            ).filter(has_undeleted=False, has_any_debt=True)
        else:
            qs = base_qs.filter(product_batches__merchantdebt__deleted=False).distinct()

        qs = (
            qs.annotate(
                initial_amount=Sum(
                    "product_batches__merchantdebt__initial_amount",
                    filter=Q(product_batches__merchantdebt__deleted=deleted),
                ),
                debt_amount=Sum(
                    F("product_batches__merchantdebt__initial_amount")
                    - F("product_batches__merchantdebt__paid_amount"),
                    filter=Q(product_batches__merchantdebt__deleted=deleted),
                    output_field=IntegerField(),
                ),
            )
            .prefetch_related(
                Prefetch(
                    "product_batches__merchantdebt",
                    queryset=MerchantDebt.objects.filter(deleted=deleted),
                    to_attr="filtered_merchantdebt",
                )
            )
            .order_by("-created_at")
        )

        page = self.paginate_queryset(qs)
        if page is not None:
            serializer = self.get_serializer(page, many=True)
            return self.get_paginated_response(serializer.data)

        serializer = self.get_serializer(qs, many=True)
        return Response(serializer.data, status=status.HTTP_200_OK)


class MerchantProductDebtDetailAPIView(GenericAPIView):
    permission_classes = [IsAuthenticated]
    serializer_class = ProductBatchDetailSerializer
    pagination_class = GlobalPagination

    def get(self, request, product_id, *args, **kwargs):
        deleted_param = request.query_params.get("deleted", "false").lower()
        deleted = deleted_param in ["1", "true", "yes"]

        # Annotate effective debt amount
        batches = ProductBatch.objects.select_related("merchantdebt").filter(
            product__id=product_id, merchantdebt__deleted=deleted
        )
        page = self.paginate_queryset(batches)
        if page is not None:
            serializer = self.get_serializer(
                page, many=True, context={"request": request}
            )
            return self.get_paginated_response(serializer.data)

        serializer = self.get_serializer(
            batches, many=True, context={"request": request}
        )
        return Response(serializer.data, status=status.HTTP_200_OK)



class SendDebtorMessagesView(generics.GenericAPIView):
    """
    POST /api/debtors/send-messages/
    Sends SMS to all debtors with has_debt=True
    """
    def post(self, request, *args, **kwargs):
        message = request.data.get("message")
        if not message:
            return Response({"error": "Message is required"}, status=status.HTTP_400_BAD_REQUEST)

        debtors = Debtor.objects.filter(has_debt=True)
        results = []

        for debtor in debtors:
            payload = {
                "to": debtor.phone_number,
                "message": message
            }
            headers = {
                "Authorization": f"Bearer {settings.TEXTBEE_API_KEY}",
                "Content-Type": "application/json"
            }

            try:
                r = requests.post(settings.TEXTBEE_API_URL, json=payload, headers=headers)
                results.append({
                    "phone_number": debtor.phone_number,
                    "status": r.status_code,
                    "response": r.json() if r.content else {}
                })
            except Exception as e:
                results.append({
                    "phone_number": debtor.phone_number,
                    "error": str(e)
                })

        return Response({"results": results}, status=status.HTTP_200_OK)
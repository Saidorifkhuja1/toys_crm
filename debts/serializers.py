from members.serializers import UserSerializer
from products.serializers import ReadProductPaymentSerializer
from rest_framework import serializers
from django.db import models

from core.serializers import BaseModelSerializer, BaseSerializer, LimitedListSerializer
from core.utils import base_read_only_fields
from core.serializers import SalePaymentSerializer
from products.models import ProductBatch
from sales.models import Payment, SalePayment
from core.serializers import WritePaymentSerializer
from .models import SaleDebt, Debtor


class SaleDebtSerializer(BaseModelSerializer):
    amount = serializers.IntegerField()
    merchant = serializers.CharField(source="sale.merchant.full_name", read_only=True)
    item_count = serializers.SerializerMethodField()
    items = serializers.SerializerMethodField()
    payments = serializers.SerializerMethodField()

    class Meta:
        model = SaleDebt
        fields = [
            "id",
            "debtor",
            "sale",
            "amount",
            "merchant",
            "item_count",
            "payments",
            "items",
            "created_at",
            "initial_amount",
        ]
        read_only_fields = base_read_only_fields

    def get_item_count(self, obj):
        if not obj.sale:
            return 0
        return obj.sale.items.aggregate(total=models.Sum("quantity"))["total"] or 0

    def get_items(self, obj):
        if not obj.sale or not hasattr(obj.sale, "items"):
            return []
        items = obj.sale.items.all()
        return [
            {
                "id": item.product.id,
                "product_type": item.product.product_type,
                "name": item.product.name,
                "price": (
                    item.product.product_batches.last().sell_price
                    if item.product.product_batches.exists()
                    else None
                ),
                "quantity": item.quantity,
                "created_at": item.created_at,
            }
            for item in items
        ]

    def get_payments(self, obj):
        if not obj.sale:
            sale_payments = SalePayment.objects.filter(
                debtor=obj.debtor, sale=None, deleted=False
            )
        else:
            sale_payments = SalePayment.objects.filter(sale=obj.sale, deleted=False)
        payments = Payment.objects.filter(sale_payment__in=sale_payments, deleted=False)
        return WritePaymentSerializer(payments, many=True).data


class DebtorSerializer(BaseModelSerializer):
    debt = SaleDebtSerializer(write_only=True, required=False)

    class Meta:
        model = Debtor
        list_serializer_class = LimitedListSerializer
        fields = "__all__"
        read_only_fields = base_read_only_fields


class PayDebtSerializer(BaseSerializer):
    debt_id = serializers.IntegerField(allow_null=True, required=False)
    debtor_id = serializers.IntegerField()
    sale_id = serializers.IntegerField(required=False, allow_null=True)
    payments = SalePaymentSerializer(many=True)
    exchange_rate = serializers.IntegerField(required=False, allow_null=True)

    def validate_payments(self, value):
        if not value:
            raise serializers.ValidationError("Kamida bitta to'lov kiritilishi kerak.")

        # Check if USD payment exists and exchange_rate is provided
        has_usd_payment = any(payment["method"] == "usd" for payment in value)
        if has_usd_payment and not self.initial_data.get("exchange_rate"):
            raise serializers.ValidationError(
                "USD to'lovi uchun almashuv kursi kiritilishi kerak!"
            )

        return value


class ProductDebtSummarySerializer(serializers.Serializer):
    id = serializers.IntegerField()
    name = serializers.CharField()
    sku = serializers.CharField()
    product_type = serializers.CharField()
    category_name = serializers.SerializerMethodField()
    supplier_name = serializers.SerializerMethodField()
    supplier_phone = serializers.SerializerMethodField()
    initial_amount = serializers.IntegerField()
    debt_amount = serializers.IntegerField()

    def get_supplier_name(self, obj):
        return obj.supplier.full_name

    def get_supplier_phone(self, obj):
        return obj.supplier.phone_number

    def get_category_name(self, obj):
        return obj.category.name


class ProductBatchDetailSerializer(BaseModelSerializer):
    merchant = UserSerializer(read_only=True)
    product_batch_payments = ReadProductPaymentSerializer(many=True, read_only=True)
    debt_amount = serializers.SerializerMethodField()
    initial_amount = serializers.SerializerMethodField()

    class Meta:
        model = ProductBatch
        # include all batch fields plus debt_amount
        fields = [
            "id",
            "buy_price",
            "deleted",
            "product_batch_payments",
            "product",
            "quantity",
            "created_at",
            "sell_price",
            "merchant",
            "debt_amount",
            "initial_amount",
        ]
        read_only_fields = base_read_only_fields

    def get_debt_amount(self, obj):
        if hasattr(obj, "merchantdebt") and obj.merchantdebt:
            return obj.merchantdebt.initial_amount - obj.merchantdebt.paid_amount
        return None

    def get_initial_amount(self, obj):
        if hasattr(obj, "merchantdebt") and obj.merchantdebt:
            return obj.merchantdebt.initial_amount
        return None

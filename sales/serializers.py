from rest_framework import serializers

from core.serializers import BaseSerializer, WritePaymentSerializer
from debts.models import Debtor
from debts.serializers import DebtorSerializer
from user.serializers import UserSerializer
from products.models import Product
from products.serializers import ProductBatchSerializer, ProductSerializer
from sales.models import Payment


class ItemSerializer(BaseSerializer):
    product_id = serializers.PrimaryKeyRelatedField(
        queryset=Product.objects.filter(deleted=False), write_only=True
    )
    quantity = serializers.IntegerField()
    product = ProductSerializer(read_only=True)

    product_batches = ProductBatchSerializer(read_only=True, many=True)


class SaleSerializer(BaseSerializer):
    id = serializers.IntegerField(read_only=True)
    created_at = serializers.DateTimeField(read_only=True)
    items = ItemSerializer(many=True)
    payments = serializers.SerializerMethodField()
    payment = WritePaymentSerializer(many=True, write_only=True)
    debtor_id = serializers.PrimaryKeyRelatedField(
        queryset=Debtor.objects.filter(deleted=False),
        required=False,
        allow_null=True,
        write_only=True,
    )
    exchange_rate = serializers.IntegerField(
        default=None, required=False, allow_null=True
    )
    total_sold = serializers.IntegerField(required=True)

    # Read-only fields
    total_paid = serializers.IntegerField(read_only=True)
    merchant = UserSerializer(read_only=True)
    debtor = DebtorSerializer(read_only=True)

    def get_payments(self, obj):
        # Get all Payment objects via SalePayment → Payment
        payments_qs = Payment.objects.filter(sale_payment__sale=obj, deleted=False)
        return WritePaymentSerializer(payments_qs, many=True).data


class DashboardIncomeViewSerializer(serializers.Serializer):
    pure_income = serializers.IntegerField()
    income = serializers.IntegerField()
    product_count = serializers.IntegerField()
    sales_count = serializers.IntegerField()
    debt_amount = serializers.IntegerField()
    merchant_debt_amount = serializers.IntegerField()
    total_product_count = serializers.IntegerField()
    total_product_weight = serializers.IntegerField()
    members_count = serializers.IntegerField()
    admin_count = serializers.IntegerField()
    supplier_count = serializers.IntegerField()
    income_today = serializers.IntegerField()
    pure_income_today = serializers.IntegerField()
    sales_count_today = serializers.IntegerField()
    debt_amount_today = serializers.IntegerField()
    merchant_debt_today = serializers.IntegerField()
    low_stock_count = serializers.IntegerField()
    out_of_stock_count = serializers.IntegerField()
    top_selling_products = serializers.IntegerField()




class EmptySerializer(serializers.Serializer):
    pass


class PaymentSerializer(serializers.ModelSerializer):
    class Meta:
        model = Payment
        fields = "__all__"
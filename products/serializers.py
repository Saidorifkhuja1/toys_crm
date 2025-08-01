from rest_framework import serializers
from django.db import transaction

from core.utils import base_read_only_fields
from core.serializers import BaseModelSerializer, BaseSerializer, LimitedListSerializer
from core.serializers import SalePaymentSerializer as ProductPaymentSerializer
from .models import Category, Product, ProductBatch, ProductPayments
from members.serializers import SupplierSerializer


class WriteProductPaymentSerializer(BaseSerializer):
    exchange_rate = serializers.IntegerField(required=True)
    payments = ProductPaymentSerializer(many=True, required=False)


class ReadProductPaymentSerializer(BaseModelSerializer):
    class Meta:
        model = ProductPayments
        fields = "__all__"


class ProductBatchSerializer(BaseModelSerializer):
    product_batch_payments = ReadProductPaymentSerializer(many=True, read_only=True)
    payment = WriteProductPaymentSerializer(required=False, write_only=True)

    class Meta:
        model = ProductBatch
        fields = "__all__"
        read_only_fields = base_read_only_fields
        extra_kwargs = {
            "product": {"required": False},
        }


class MediaSerializer(serializers.Serializer):
    image = serializers.ImageField(write_only=True)
    product_id = serializers.PrimaryKeyRelatedField(
        queryset=Product.objects.filter(deleted=False),
        source="product",
        write_only=True,
    )


class CategorySerializer(BaseModelSerializer):
    class Meta:
        model = Category
        fields = ["name", "id", "created_at", "updated_at", "created_by", "updated_by"]
        read_only_fields = base_read_only_fields
        list_serializer_class = LimitedListSerializer


class ProductSerializer(BaseModelSerializer):
    product_batches = ProductBatchSerializer(
        many=True, context={"exclude_product": True}, read_only=True
    )
    product_batch = ProductBatchSerializer(
        write_only=True, context={"exclude_product": True}, required=False
    )
    total_quantity = serializers.IntegerField(read_only=True)
    sell_price = serializers.IntegerField(read_only=True)
    # supplier_id = ZeroToNullPrimaryKeyField(
    #     queryset=Supplier.objects.filter(deleted=False),
    #     source="supplier",
    #     write_only=True,
    # )
    supplier = SupplierSerializer(read_only=True)
    category = CategorySerializer(read_only=True)
    category_id = serializers.PrimaryKeyRelatedField(
        queryset=Category.objects.filter(deleted=False),
        source="category",
        write_only=True,
        required=False,
    )

    class Meta:
        model = Product
        fields = "__all__"
        read_only_fields = base_read_only_fields + [
            "sku",
            "total_quantity",
            "product_batches",
            "sell_price",
            "supplier",
            "category",
        ]
        list_serializer_class = LimitedListSerializer

    def to_representation(self, instance):
        """Add total quantity of product batches to product response data"""
        if instance.product_batches.exists():
            total_quantity = sum(
                batch.quantity
                for batch in instance.product_batches.filter(deleted=False)
            )
            instance.total_quantity = total_quantity
            instance.sell_price = instance.product_batches.last().sell_price
        return super().to_representation(instance)


class ProductForSaleSerializer(ProductSerializer):
    total_quantity = serializers.IntegerField(read_only=True)
    category = CategorySerializer(read_only=True)

    class Meta:
        fields = "__all__"
        model = Product
        fields = [
            "id",
            "name",
            "total_quantity",
            "sell_price",
            "image",
            "created_at",
            "category",
        ]
        listdir_serializer_class = LimitedListSerializer

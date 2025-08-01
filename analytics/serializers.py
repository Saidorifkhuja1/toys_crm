from rest_framework import serializers

from products.models import Product


class DashboardCountsSerializer(serializers.Serializer):
    product_count = serializers.IntegerField()
    product_batch_count = serializers.IntegerField()
    supplier_count = serializers.IntegerField()
    merchant_count = serializers.IntegerField()
    admin_count = serializers.IntegerField()
    category_count = serializers.IntegerField()
    sale_count = serializers.IntegerField()


class TotalSerializer(serializers.Serializer):
    total = serializers.DecimalField(max_digits=20, decimal_places=2)


class AssetValueSerializer(serializers.Serializer):
    total = serializers.IntegerField()


class LowStockProductSerializer(serializers.ModelSerializer):
    count = serializers.IntegerField(read_only=True)

    class Meta:
        model = Product
        fields = ("id", "name", "count")


class OutOfStockProductSerializer(serializers.ModelSerializer):
    class Meta:
        model = Product
        fields = ("id", "name")


class TopSellingProductSerializer(serializers.ModelSerializer):
    sale_count = serializers.IntegerField(read_only=True)

    class Meta:
        model = Product
        fields = ("id", "name", "sale_count")

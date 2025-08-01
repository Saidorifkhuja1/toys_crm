from rest_framework import serializers

from core.serializers import BaseSerializer


class UnifiedLogSerializer(BaseSerializer):
    id = serializers.IntegerField()
    type = serializers.CharField()
    action = serializers.CharField()
    created_at = serializers.DateTimeField()
    created_by = serializers.StringRelatedField()
    note = serializers.CharField()
    sku = serializers.SerializerMethodField()
    author = serializers.SerializerMethodField()
    product_name = serializers.SerializerMethodField()

    def get_sku(self, obj):
        if hasattr(obj, "product") and obj.product:
            return obj.product.sku
        elif hasattr(obj, "batch") and obj.batch and obj.batch.product:
            return obj.batch.product.sku
        return None

    def get_author(self, obj):
        return getattr(obj.created_by, "full_name", None)

    def get_product_name(self, obj):
        if hasattr(obj, "product") and obj.product:
            return obj.product.name
        elif hasattr(obj, "batch") and obj.batch and obj.batch.product:
            return obj.batch.product.name
        return None

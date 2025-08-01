from rest_framework import serializers

from core.enums import PaymentType
from sales.models import Payment


class LimitedListSerializer(serializers.ListSerializer):
    """
    Truncate any list of objects to at most `max_length` items.
    """

    max_length = 8

    def to_representation(self, data):
        if hasattr(data, "all"):
            # If it's a manager or queryset, slice at DB level
            data = data.all()[: self.max_length]
        elif isinstance(data, list):
            # If already a list, slice in memory
            data = data[: self.max_length]
        return super().to_representation(data)


class BaseSerializer(serializers.Serializer):
    """Custom Serializer to remove field deleted"""

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.fields.pop("deleted", None)


class BaseModelSerializer(serializers.ModelSerializer, BaseSerializer):
    """Custom Model Serializer to remove field deleted"""


class SalePaymentSerializer(serializers.Serializer):
    method = serializers.ChoiceField(choices=PaymentType.choices)
    amount = serializers.IntegerField()


class WritePaymentSerializer(BaseModelSerializer):
    class Meta:
        model = Payment
        fields = ["method", "amount", "created_at", "created_by", "id"]
        read_only_fields = ["created_at", "created_by", "id"]

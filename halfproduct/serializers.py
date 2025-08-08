from rest_framework import serializers
from .models import HalfProduct

class HalfProductSerializer(serializers.ModelSerializer):
    class Meta:
        model = HalfProduct
        fields = '__all__'
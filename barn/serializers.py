from rest_framework import serializers


from .models import Barn


class BarnSerializer(serializers.ModelSerializer):
    class Meta:
        model = Barn
        fields = ['uid', 'name', 'location']
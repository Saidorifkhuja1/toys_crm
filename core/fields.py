from rest_framework import serializers

class ZeroToNullPrimaryKeyField(serializers.PrimaryKeyRelatedField):
    def to_internal_value(self, data):
        if data == 0:
            return None
        return super().to_internal_value(data)
    
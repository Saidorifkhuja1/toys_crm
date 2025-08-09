from rest_framework import serializers
from .models import Worker



class WorkerSerializer(serializers.ModelSerializer):
    class Meta:
        model = Worker

        exclude = ['paid_salary']

class WorkerSerializer1(serializers.ModelSerializer):
    class Meta:
        model = Worker
        fields = ['uid', 'name', 'last_name', 'phone_number', 'salary', 'paid_salary', 'unpaid_salary']

    def to_representation(self, instance):
        representation = super().to_representation(instance)
        representation['unpaid_salary'] = instance.salary - instance.paid_salary
        return representation
# class WorkerSalaryPaymentSerializer(serializers.Serializer):
#     amount = serializers.DecimalField(max_digits=12, decimal_places=2)
#
#     def validate_amount(self, value):
#         if value <= 0:
#             raise serializers.ValidationError("Amount must be greater than zero.")
#         return value
#
#     def update(self, instance, validated_data):
#         amount = validated_data['amount']
#         instance.paid_salary += amount
#         instance.save()
#         return instance


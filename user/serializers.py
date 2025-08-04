from rest_framework import serializers
from core.serializers import BaseModelSerializer, LimitedListSerializer
from core.utils import base_read_only_fields
from user.models import Supplier, User


class UserSerializer(serializers.ModelSerializer):
    class Meta:
        model = User
        fields = [
            "id",
            "is_superuser",
            "username",
            "is_staff",
            "is_active",
            "phone_number",
            "date_joined",
            "full_name",
            "user_role",
            "password",
        ]
        read_only_fields = (
            "id",
            "date_joined",
            "is_active",
            "is_staff",
            "is_superuser",
            "first_name",
            "user_role",
            "last_name",
            "email",
            "groups",
            "user_permissions",
            "last_login",
        )
        extra_kwargs = {"password": {"write_only": True}}

    def create(self, validated_data):
        print("Creating user with data:", validated_data)
        user = User.objects.create_user(user_role="Merchant", **validated_data)
        return user

    def validate_phone_number(self, value):
        user_id = self.instance.id if self.instance else None
        if (
            User.objects.filter(phone_number=value, is_active=True)
            .exclude(id=user_id)
            .exists()
        ):
            raise serializers.ValidationError("Bu raqam allaqachon mavjud.")
        return value

    def validate_username(self, value):
        user_id = self.instance.id if self.instance else None
        if (
            User.objects.filter(username=value, is_active=True)
            .exclude(id=user_id)
            .exists()
        ):
            raise serializers.ValidationError(
                "Bu foydalanuvchi nomi allaqachon mavjud."
            )
        return value


class LoginSerializer(serializers.Serializer):
    username = serializers.CharField(max_length=150)
    password = serializers.CharField(max_length=128, write_only=True)

    def validate(self, attrs):
        username = attrs.get("username")
        password = attrs.get("password")

        if not username or not password:
            raise serializers.ValidationError(
                "Both username and password are required."
            )

        return attrs


class SupplierSerializer(BaseModelSerializer):
    debt = serializers.IntegerField(read_only=True)

    class Meta:
        fields = "__all__"
        model = Supplier
        read_only_fields = base_read_only_fields
        list_serializer_class = LimitedListSerializer

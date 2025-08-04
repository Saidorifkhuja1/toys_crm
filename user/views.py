from django.db import IntegrityError
from django.db.models import (
    Sum,
    F,
    ExpressionWrapper,
    IntegerField,
    Q,
    Exists,
    OuterRef,
)
from rest_framework.generics import GenericAPIView
from rest_framework_simplejwt.tokens import RefreshToken
from rest_framework.permissions import AllowAny
from rest_framework.decorators import api_view, permission_classes
from rest_framework.permissions import IsAuthenticated
from rest_framework.response import Response
from rest_framework.request import Request
from rest_framework import status
from rest_framework.exceptions import ValidationError
from rest_framework_simplejwt.views import TokenObtainPairView, TokenRefreshView
from rest_framework_simplejwt.serializers import (
    TokenObtainPairSerializer,
    TokenRefreshSerializer,
)
from core.viewsets import CoreViewSet, UpdateMessageMixin
from user.serializers import UserSerializer
from debts.models import MerchantDebt
from .serializers import SupplierSerializer
from user.models import Supplier, User
from core.permissions import IsAdminUser


class RegisterView(GenericAPIView):
    serializer_class = UserSerializer
    model = User
    permission_classes = [AllowAny]

    def post(self, request):
        userDetails = self.get_serializer(data=request.data)
        userDetails.is_valid(raise_exception=True)
        try:
            userDetails.validated_data["user_role"] = "Admin"
            userDetails.validated_data["is_active"] = True
            userDetails.validated_data["is_superuser"] = True
            user = self.model.objects.create_user(**userDetails.validated_data)
        except Exception as e:
            return Response({"error": str(e)}, status=status.HTTP_400_BAD_REQUEST)

        refresh = RefreshToken.for_user(user)
        return Response(
            {
                "message": "Ro'yxatdan o'tish muvaffaqiyatli amalga oshirildi",
                "access": str(refresh.access_token),
                "refresh": str(refresh),
            },
            status=status.HTTP_201_CREATED,
        )


class SupplierViewSet(CoreViewSet):
    queryset = Supplier.objects.all().order_by("-created_at")
    permission_classes = [IsAuthenticated]
    serializer_class = SupplierSerializer
    search_fields = ["full_name", "phone_number"]

    def perform_destroy(self, instance):
        merchant_debts = MerchantDebt.objects.filter(
            product_batch__product__supplier__id=instance.id, deleted=False
        )
        if merchant_debts.exists():
            raise ValidationError(
                {"error": "Ushbu yetkazib beruvchini sotuvchilardan haqqi bor"}
            )
        return super().perform_destroy(instance)

    def get_queryset(self):
        deleted_param = self.request.query_params.get("deleted", False)
        deleted = deleted_param in ["true", "yes", "1"]
        # debt_mode = self.request.query_params.get("debt_mode", False)
        # debt_mode = debt_mode in ["true", "yes", "1"]
        qs = (
            Supplier.objects.filter(deleted=deleted)
            .annotate(
                debt=Sum(
                    ExpressionWrapper(
                        F("product__product_batches__merchantdebt__initial_amount")
                        - F("product__product_batches__merchantdebt__paid_amount"),
                        output_field=IntegerField(),
                    ),
                    filter=Q(product__product_batches__merchantdebt__deleted=False),
                )
            )
            .order_by("-created_at")
        )
        # if debt_mode:
        #     # Subquery to check if merchant debt exists for any product of supplier
        #     has_debt_subquery = MerchantDebt.objects.filter(
        #         product_batch__product__supplier=OuterRef("pk"), deleted=False
        #     )
        #     qs = qs.annotate(has_debt=Exists(has_debt_subquery)).filter(has_debt=True)

        return qs


class CustomTokenObtainPairView(TokenObtainPairView, UpdateMessageMixin):
    serializer_class = TokenObtainPairSerializer


class CustomTokenRefreshView(TokenRefreshView, UpdateMessageMixin):
    serializer_class = TokenRefreshSerializer


@api_view(["PATCH"])
@permission_classes([IsAuthenticated])
def update_profile(request: Request):
    try:
        user = User.objects.get(id=request.user.id)
        username, full_name, phone_number, email = (
            request.data.get("username", None),
            request.data.get("full_name", None),
            request.data.get("phone_number", None),
            request.data.get("email", None),
        )
        if full_name:
            user.full_name = full_name
        if username:
            user.username = username
        if phone_number:
            user.phone_number = phone_number
        if email:
            user.email = email
        user.save()
        return Response(
            {"message": "Profile updated successfully"},
            status=status.HTTP_200_OK,
        )
    except User.DoesNotExist:
        return Response(
            {"error": "User not found"},
            status=status.HTTP_404_NOT_FOUND,
        )
    except IntegrityError:
        return Response(
            {
                "error": "Kiritilgan telefon raqam yoki foydalanuvchi nomi allaqachon mavjud!"
            },
            status=status.HTTP_400_BAD_REQUEST,
        )
    except Exception as e:
        return Response(
            {"error": str(e)},
            status=status.HTTP_500_INTERNAL_SERVER_ERROR,
        )


@api_view(["GET"])
@permission_classes([IsAuthenticated])
def get_user_profile(request: Request):
    try:
        user = User.objects.get(id=request.user.id)
        serializer = UserSerializer(user)
        return Response(serializer.data, status=status.HTTP_200_OK)
    except User.DoesNotExist:
        return Response(
            {"error": "User not found"},
            status=status.HTTP_404_NOT_FOUND,
        )
    except Exception as e:
        return Response(
            {"error": str(e)},
            status=status.HTTP_400_BAD_REQUEST,
        )


class MerchantViewSet(CoreViewSet):
    permission_classes = [IsAdminUser]
    queryset = User.objects.filter(is_active=True).order_by("-date_joined")
    serializer_class = UserSerializer
    search_fields = ["full_name", "phone_number"]

    def get_queryset(self):
        return self.queryset

    def perform_destroy(self, instance):
        instance.is_active = False
        instance.username = f"{instance.username}_deleted_{instance.id}"
        instance.save()

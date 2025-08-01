from rest_framework.permissions import BasePermission

from core.enums import UserRole


class IsAdminUser(BasePermission):
    """
    Custom permission to only allow admin users to access the view.
    """

    def has_permission(self, request, view):
        return (
            request.user
            and request.user.is_superuser
            and request.user.user_role == UserRole.ADMIN
        )


class IsMerchant(BasePermission):
    def has_permission(self, request, view):
        return request.user and request.user.user_role == UserRole.MERCHANT

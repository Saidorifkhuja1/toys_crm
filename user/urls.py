from django.urls import path

from user.views import (
    CustomTokenObtainPairView,
    CustomTokenRefreshView,
    get_user_profile,
    RegisterView,
    update_profile,
)

urlpatterns = [
    path("register/", RegisterView.as_view(), name="register"),
    path("token/refresh/", CustomTokenRefreshView.as_view(), name="token_refresh"),
    path("token/", CustomTokenObtainPairView.as_view(), name="token_pair"),
    path("update-profile/", update_profile, name="update_profile"),
    path("me/", get_user_profile, name="get_user_profile"),
]

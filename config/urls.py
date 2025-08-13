
from django.conf import settings
from django.conf.urls.static import static
from django.contrib import admin
from django.urls import path, include
from django.views.generic import TemplateView


from drf_yasg import openapi
from drf_yasg.views import get_schema_view

from rest_framework import permissions
from rest_framework.routers import DefaultRouter

from logs.views import LogViewSet
from user.views import MerchantViewSet, SupplierViewSet
from products.views import (
    MediaCreateView,
    MediaDeleteView,
    get_count,
    ProductForSaleViewSet,
    ProductBatchViewSet,
    CategoryViewSet,
    ProductViewSet,
)

# schema_view = get_schema_view(
#     openapi.Info(
#         title="Your API",
#         default_version="v1",
#         description="Your API description",
#         terms_of_service="https://www.google.com/policies/terms/",
#         contact=openapi.Contact(email="contact@yourdomain.com"),
#         license=openapi.License(name="BSD License"),
#     ),
#     public=True,
#     permission_classes=(permissions.AllowAny,),
#     authentication_classes=[],
# )
schema_view = get_schema_view(
    openapi.Info(
        title="Your API",
        default_version="v1",
        description="Your API description",
        terms_of_service="https://www.google.com/policies/terms/",
        contact=openapi.Contact(email="contact@yourdomain.com"),
        license=openapi.License(name="BSD License"),
    ),
    public=True,
    permission_classes=(permissions.AllowAny,),
)

product_list_create = ProductViewSet.as_view({"get": "list", "post": "create"})
product_detail = ProductViewSet.as_view(
    {"get": "retrieve", "patch": "partial_update", "delete": "destroy"}
)

router = DefaultRouter()
router.register(r"suppliers", SupplierViewSet)
# router.register(r"products", ProductViewSet, basename="product")
router.register(r"product-batch", ProductBatchViewSet, basename="product-batch")
router.register(r"categories", CategoryViewSet, basename="category")
router.register(r"merchants", MerchantViewSet, basename="merchant")
router.register(r"sale-products", ProductForSaleViewSet, basename="product-for-sale")
router.register(r"logs", LogViewSet, basename="logs")

urlpatterns = [
    path('admin/', admin.site.urls),
    path("products/write-read/<int:supplier_id>/",product_list_create,name="supplier-product-list",),
    path("products/modify/<str:sku>/", product_detail, name="product-detail"),
    path("", include("django_prometheus.urls")),
    path("auth/", include("user.urls")),
    path("barn/", include("barn.urls")),
    path("halfproduct/", include("halfproduct.urls")),
    path("workers/", include("workers.urls")),
    path("analytics/", include("analytics.urls")),
    path("sales/", include("sales.urls")),
    path("", include("debts.urls")),
    path("", include(router.urls)),
    path("count/", get_count),
    path(
        "docs/",
        TemplateView.as_view(template_name="swagger/swagger-ui.html"),
        name="custom-swagger-ui",
    ),
    # path('docs/', schema_view.with_ui('swagger', cache_timeout=0), name='schema-swagger-ui'),
    path("swagger.json/", schema_view.without_ui(cache_timeout=0), name="schema-json"),
    path("media/upload/", MediaCreateView.as_view()),
    path("media/delete/<int:pk>/", MediaDeleteView.as_view()),
]

urlpatterns += static(settings.STATIC_URL, document_root=settings.STATIC_ROOT)
urlpatterns += static(settings.MEDIA_URL, document_root=settings.MEDIA_ROOT)



import django_filters
from products.models import Product
from core.filters import BaseDateFilter  # adjust path as needed


class ProductFilter(BaseDateFilter):
    product_type = django_filters.ChoiceFilter(
        field_name="product_type", choices=Product.ProductType
    )
    name = django_filters.CharFilter(field_name="name", lookup_expr="icontains")
    category = django_filters.CharFilter(
        field_name="category__name", lookup_expr="icontains"
    )

    class Meta:
        model = Product
        fields = [
            "created_day",
            "created_year",
            "created_month",
            "product_type",
            "name",
            "category",
        ]

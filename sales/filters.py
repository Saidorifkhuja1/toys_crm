from django_filters.rest_framework import CharFilter
from sales.models import Sale
from core.filters import BaseDateFilter

class SaleFilter(BaseDateFilter):
    payment_type = CharFilter(method="filter_payment_type")

    def filter_payment_type(self, queryset, name, value):
        if value == "card":
            return queryset.filter(
                payment__payments__method='card',
                payment__payments__amount__gt=0
            )
        elif value == "uzs":
            return queryset.filter(
                payment__payments__method='uzs',
                payment__payments__amount__gt=0
            )
        elif value == "debt":
            return queryset.filter(
                payment__payments__method='debt',
                payment__payments__amount__gt=0
            )
        return queryset

    class Meta:
        model = Sale
        fields = [
            "created_day",
            "created_year",
            "created_month",
            "payment_type",
        ]

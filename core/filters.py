from datetime import timedelta
from django_filters import rest_framework as filters


class BaseDateFilter(filters.FilterSet):
    created_day = filters.NumberFilter(field_name="created_at", lookup_expr="day")
    created_month = filters.NumberFilter(field_name="created_at", lookup_expr="month")
    created_year = filters.NumberFilter(field_name="created_at", lookup_expr="year")
    start_date = filters.DateFilter(field_name="created_at", lookup_expr="gte")
    end_date = filters.DateFilter(method="filter_end_date")
    created_at = filters.DateTimeFromToRangeFilter(
        field_name="created_at", lookup_expr="range"
    )

    class Meta:
        abstract = True
        fields = [
            "created_at",
            "created_day",
            "created_month",
            "created_year",
            "start_date",
            "end_date",
        ]

    def filter_end_date(self, queryset, name, value):
        # include the entire `value`-day by going up to but not including next midnight
        next_day = value + timedelta(days=1)
        return queryset.filter(created_at__lt=next_day)

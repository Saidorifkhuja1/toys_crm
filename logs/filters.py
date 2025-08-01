# from django_filters import rest_framework as filters
# from core.filters import BaseDateFilter
# from logs.models import ProductLog
# from core.enums import Actions


# class InventoryLogFilter(BaseDateFilter):
#     ACTION_ALL = "all"
#     VALID_ACTIONS = {label.lower(): value for value, label in Actions.choices}

#     # use CharFilter so Django-Filters won’t pre-validate against only the enum choices
#     action = filters.CharFilter(method="filter_action")

#     class Meta:
#         model = ProductLog
#         fields = [
#             "created_day",
#             "created_month",
#             "created_year",
#             "action",
#         ]

#     def filter_action(self, queryset, name, value):
#         val = value.strip().lower()
#         if val == self.ACTION_ALL:
#             # “all” → no filtering
#             return queryset
#         if val in self.VALID_ACTIONS:
#             # map back to the stored value and do iexact
#             real_value = self.VALID_ACTIONS[val]
#             return queryset.filter(**{f"{name}__iexact": real_value})
#         # invalid action → empty result set (or you could raise a ValidationError)
#         return queryset.none()

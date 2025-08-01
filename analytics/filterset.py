from core.filters import BaseDateFilter
from debts.models import MerchantDebt, SaleDebt
from sales.models import Sale


class SaleDebtFilter(BaseDateFilter):
    class Meta(BaseDateFilter.Meta):
        model = SaleDebt
        fields = BaseDateFilter.Meta.fields


class MerchantDebtFilter(BaseDateFilter):
    class Meta(BaseDateFilter.Meta):
        model = MerchantDebt
        fields = BaseDateFilter.Meta.fields


class IncomeFilter(BaseDateFilter):
    class Meta:
        model = Sale
        fields = BaseDateFilter.Meta.fields

from django.utils import timezone
from sales.models import Sale, SaleItemBatch


def calculate_monthly_income():
    """
    Calculate the total income from sales for the current month.
    This function sums up the total price of all sales made in the current month.
    """

    now = timezone.now()
    start_of_month = now.replace(day=1, hour=0, minute=0, second=0, microsecond=0)
    monthly_sales = Sale.objects.filter(created_at__gte=start_of_month, deleted=False)
    total_income = sum(sale.total_sold for sale in monthly_sales)

    return total_income


def after_product_prices():
    """
    Calculate the personal income from product sales for the current month.
    Formula:
        (sell_price - buy_price) * quantity_used
    Aggregated across all SaleItemBatch records of the current month.
    """

    now = timezone.now()
    start_of_month = now.replace(day=1, hour=0, minute=0, second=0, microsecond=0)

    batches = SaleItemBatch.objects.filter(
        created_at__gte=start_of_month, deleted=False
    ).select_related("product_batch")

    total_profit = 0
    for batch in batches:
        profit_per_unit = batch.product_batch.sell_price - batch.product_batch.buy_price
        total_profit += profit_per_unit * batch.quantity_used

    return total_profit

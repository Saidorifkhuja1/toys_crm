from django.db import models

from core.models import BaseCreateModel
from core.enums import PaymentType, UserRole


class Sale(BaseCreateModel):
    merchant = models.ForeignKey(
        "members.User",
        on_delete=models.SET_NULL,
        limit_choices_to={"user_role": UserRole.MERCHANT},
        related_name="sales",
        null=True,
    )
    debtor = models.ForeignKey(to="debts.Debtor", on_delete=models.SET_NULL, null=True)
    total_sold = models.PositiveBigIntegerField()
    total_paid = models.PositiveBigIntegerField(null=True)

    class Meta:
        db_table = "sales"


class SaleItem(BaseCreateModel):
    sale = models.ForeignKey(
        Sale, on_delete=models.SET_NULL, null=True, related_name="items"
    )
    product = models.ForeignKey("products.Product", on_delete=models.CASCADE, null=True)
    quantity = models.IntegerField()

    class Meta:
        db_table = "sale_items"


class SaleItemBatch(BaseCreateModel):
    sale_item = models.ForeignKey(
        SaleItem, on_delete=models.CASCADE, related_name="batches"
    )
    product_batch = models.ForeignKey("products.ProductBatch", on_delete=models.CASCADE)
    quantity_used = models.IntegerField()

    class Meta:
        db_table = "sale_item_batches"


class SalePayment(BaseCreateModel):
    sale = models.ForeignKey(
        to="Sale", on_delete=models.SET_NULL, null=True, related_name="payment"
    )
    exchange_rate = models.PositiveBigIntegerField(null=True, blank=True)
    debtor = models.ForeignKey("debts.Debtor", on_delete=models.SET_NULL, null=True)

    class Meta:
        db_table = "sale_payments"


class Payment(BaseCreateModel):
    sale_payment = models.ForeignKey(
        "SalePayment", on_delete=models.CASCADE, related_name="payments"
    )
    method = models.CharField(choices=PaymentType.choices)
    amount = models.PositiveBigIntegerField()

    class Meta:
        db_table = "payments"

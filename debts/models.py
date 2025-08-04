from django.db import models

from core.models import BaseCreateModel, BaseModel


class Debtor(BaseModel):
    phone_number = models.CharField(max_length=40, unique=True, null=False)
    full_name = models.CharField(max_length=130)
    has_debt = models.BooleanField(default=False)

    class Meta:
        db_table = "debtors"


class SaleDebt(BaseCreateModel):
    debtor = models.ForeignKey(Debtor, on_delete=models.CASCADE, null=True)
    sale = models.ForeignKey(
        "sales.Sale", on_delete=models.CASCADE, related_name="debts", null=True
    )
    amount = models.PositiveBigIntegerField()
    initial_amount = models.PositiveBigIntegerField(default=0)

    class Meta:
        db_table = "sale_debts"


class MerchantDebt(BaseCreateModel):
    initial_amount = models.PositiveBigIntegerField()
    paid_amount = models.PositiveBigIntegerField()
    merchant = models.ForeignKey("user.User", on_delete=models.CASCADE)
    product_batch = models.OneToOneField(
        "products.ProductBatch", on_delete=models.CASCADE
    )

    class Meta:
        db_table = "merchant_debts"

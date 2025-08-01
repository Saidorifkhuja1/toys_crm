from django.db import models

from core.enums import PaymentType
from core.models import BaseCreateModel, BaseModel
from products.utils import generate_sku, product_image_upload_path


class Category(BaseModel):
    """
    Model representing a product category.
    """

    name = models.CharField(max_length=255, unique=True)

    def __str__(self):
        return self.name

    class Meta:
        db_table = "categories"


class Product(BaseModel):
    """
    Model representing a product.
    """

    ProductType = (
        ("KG", "Kilogram"),
        ("PIECE", "Piece"),
    )

    name = models.CharField(max_length=255)
    description = models.TextField(blank=True, max_length=10000)
    image = models.ImageField(
        upload_to=product_image_upload_path, blank=True, null=True
    )
    sku = models.CharField(max_length=100, default=generate_sku, unique=True)
    product_type = models.CharField(max_length=10, choices=ProductType)
    category = models.ForeignKey(Category, on_delete=models.SET_NULL, null=True)
    supplier = models.ForeignKey(
        to="members.Supplier", on_delete=models.CASCADE, null=False
    )

    def __str__(self):
        return self.name

    class Meta:
        db_table = "products"


class ProductBatch(BaseModel):
    product = models.ForeignKey(
        Product, on_delete=models.CASCADE, related_name="product_batches"
    )
    quantity = models.PositiveIntegerField()
    buy_price = models.PositiveBigIntegerField()
    sell_price = models.PositiveBigIntegerField()

    class Meta:
        db_table = "product_batches"


class ProductPayments(BaseCreateModel):
    amount = models.BigIntegerField()
    method = models.CharField(choices=PaymentType.choices)
    product_batch = models.ForeignKey(
        ProductBatch, on_delete=models.CASCADE, related_name="product_batch_payments"
    )
    exchange_rate = models.PositiveBigIntegerField(null=True)

    class Meta:
        db_table = "product_payments"

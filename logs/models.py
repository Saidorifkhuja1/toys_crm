from django.db import models
from core.models import BaseCreateModel, BaseLog


class ProductLog(BaseCreateModel, BaseLog):
    product = models.ForeignKey(to="products.Product", on_delete=models.SET_NULL, null=True)

    class Meta:
        ordering = ["-created_at"]
        indexes = [
            models.Index(fields=["product", "id", "created_at", "created_by"]),
        ]
        db_table = "product_logs"


class BatchLog(BaseCreateModel, BaseLog):
    batch = models.ForeignKey(to="products.ProductBatch", on_delete=models.SET_NULL, null=True)

    class Meta:
        ordering = ["-created_at"]
        indexes = [
            models.Index(fields=["batch", "id", "created_at", "created_by"]),
        ]
        db_table = "batch_logs"

import uuid
from barn.models import Barn
from django.db import models


class HalfProduct(models.Model):
    ProductType = (
        ("KG", "Kilogram"),
        ("PIECE", "Piece"),
        ("METR", "metr"),
    )
    uid = models.UUIDField(default=uuid.uuid4, primary_key=True)
    name = models.CharField(max_length=100)
    price = models.DecimalField(max_digits=10, decimal_places=2)
    # metr = models.IntegerField(default=0)
    # kg = models.IntegerField(default=0)
    # pieces = models.IntegerField(default=0)
    product_type = models.CharField(max_length=10, choices=ProductType)
    amount = models.DecimalField(max_digits=10, decimal_places=2)
    barn = models.ForeignKey(Barn, on_delete=models.CASCADE)

    def __str__(self):
        return self.name



import uuid
from django.db import models


class Worker(models.Model):
    uid = models.UUIDField(default=uuid.uuid4, primary_key=True)
    name = models.CharField(max_length=500)
    last_name = models.CharField(max_length=500)
    phone_number = models.CharField(max_length=40, unique=True, null=False)
    salary = models.DecimalField(max_digits=12, decimal_places=2, default=0.00)
    paid_salary = models.DecimalField(max_digits=12, decimal_places=2, default=0.00)

    def __str__(self):
        return f"{self.name} {self.last_name}"




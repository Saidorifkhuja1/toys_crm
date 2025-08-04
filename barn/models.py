import uuid
from django.db import models


class Barn(models.Model):
    uid = models.UUIDField(default=uuid.uuid4, primary_key=True)
    name = models.CharField(max_length=500)
    location = models.CharField(max_length=500)

    def __str__(self):
        return self.name

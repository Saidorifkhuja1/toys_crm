from django.db import models
from django.contrib.auth.models import AbstractUser
import uuid
from core.enums import UserRole
from core.models import BaseModel


class User(AbstractUser):
    """
    Custom user model that extends the default Django user model.
    """

    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    full_name = models.CharField(max_length=150, blank=True)
    phone_number = models.CharField(max_length=120, null=False, default="+998")
    user_role = models.CharField(choices=UserRole.choices, max_length=10, default="Admin")
    created_by = models.ForeignKey("self",on_delete=models.SET_NULL,null=True,blank=True,related_name="+",)
    updated_by = models.ForeignKey("self",on_delete=models.SET_NULL,null=True,blank=True,related_name="+",)

    def __str__(self):
        return self.username

    class Meta:
        db_table = "users"


class Supplier(BaseModel):
    """
    Model representing a supplier.
    """

    full_name = models.CharField(max_length=255)
    phone_number = models.CharField(max_length=20, unique=True)

    def __str__(self):
        return self.full_name

    class Meta:
        db_table = "suppliers"

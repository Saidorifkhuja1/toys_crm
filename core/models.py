from django.db import models

from core.enums import Actions


class BaseCreateModel(models.Model):
    created_at = models.DateTimeField(auto_now_add=True)
    created_by = models.ForeignKey(
        to="user.User",
        on_delete=models.SET_DEFAULT,
        null=True,
        related_name="created_%(class)ss",
        default=None,
    )
    deleted = models.BooleanField(default=False, null=False)

    class Meta:
        abstract = True


class BaseModel(BaseCreateModel):
    updated_at = models.DateTimeField(auto_now=True)
    updated_by = models.ForeignKey(
        to="user.User",
        on_delete=models.SET_DEFAULT,
        null=True,
        default=None,
        related_name="updated_%(class)ss",
    )

    class Meta:
        abstract = True


class BaseLog(models.Model):
    action = models.CharField(max_length=30, choices=Actions.choices, null=True)
    note = models.TextField(max_length=3000, null=True)

    class Meta:
        abstract = True

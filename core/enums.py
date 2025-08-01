from django.db import models
from enum import Enum


class UserRole(models.TextChoices):
    MERCHANT = "Merchant", "Merchant"
    ADMIN = "Admin", "Admin"


class ExtendedUserRole(models.TextChoices):
    MERCHANT = "Merchant", "Merchant"
    ADMIN = "Admin", "Admin"
    SUPPLIER = "Supplier", "Supplier"
    DEBTOR = "Debtor", "Debtor"


class UnitType(models.TextChoices):
    KG = "KG", "Kilogram"
    PIECE = "PIECE", "Piece"


class Actions(models.TextChoices):
    ADD = "Add", "Add"
    ADJUST = "Adjust", "Adjust"
    DELETE = "Delete", "Delete"


class PaymentType(models.TextChoices):
    card = "card"
    uzs = "uzs"
    usd = "usd"

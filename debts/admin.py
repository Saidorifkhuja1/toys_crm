from django.contrib import admin
from .models import Debtor



@admin.register(Debtor)
class DebtorAdmin(admin.ModelAdmin):
    list_display = ['full_name']
from django.contrib import admin
from .models import HalfProduct



@admin.register(HalfProduct)
class HalfProductAdmin(admin.ModelAdmin):
    list_display = ['name']
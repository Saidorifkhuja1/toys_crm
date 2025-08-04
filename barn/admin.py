from django.contrib import admin
from .models import Barn



@admin.register(Barn)
class BarnAdmin(admin.ModelAdmin):
    list_display = ['name']
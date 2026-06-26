from django.contrib import admin

# Register your models here.

from django.contrib import admin
from .models import Filierebts

@admin.register(Filierebts)
class FilierebtsAdmin(admin.ModelAdmin):
    list_display = ("id", "nom")
    search_fields = ("nom",)
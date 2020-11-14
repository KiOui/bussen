from django.contrib import admin
from .models import BusGameModel, Hand

# Register your models here.


@admin.register(BusGameModel)
class GameAdmin(admin.ModelAdmin):
    """Admin model for Games."""


@admin.register(Hand)
class HandAdmin(admin.ModelAdmin):
    """Admin model for Players."""

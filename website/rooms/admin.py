from django.contrib import admin
from .models import Game, Player, Hand

# Register your models here.


@admin.register(Game)
class GameAdmin(admin.ModelAdmin):
    """Admin model for Games."""


@admin.register(Player)
class PlayerAdmin(admin.ModelAdmin):
    """Admin model for Players."""


@admin.register(Hand)
class HandAdmin(admin.ModelAdmin):
    """Admin model for Players."""

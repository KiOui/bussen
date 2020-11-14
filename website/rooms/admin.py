from django.contrib import admin
from rooms.models import Player, Room


@admin.register(Player)
class PlayerAdmin(admin.ModelAdmin):
    """Admin model for Players."""


@admin.register(Room)
class RoomAdmin(admin.ModelAdmin):
    """Admin model for Rooms."""

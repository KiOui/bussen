from django.apps import AppConfig


class RoomsConfig(AppConfig):
    """Room config."""

    name = "rooms"

    def ready(self):
        """Ready method."""
        pass

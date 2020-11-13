from django.apps import AppConfig


class RoomsConfig(AppConfig):
    name = 'rooms'

    def ready(self):
        """Ready method."""
        pass
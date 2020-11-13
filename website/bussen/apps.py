from django.apps import AppConfig


class BussenConfig(AppConfig):
    """BussenConfig."""

    name = "bussen"

    def ready(self):
        from .games import games

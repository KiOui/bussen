from django.apps import AppConfig


class BussenConfig(AppConfig):
    """BussenConfig."""

    name = "bussen"

    def ready(self):
        """Ready method."""
        from .games import games  # noqa

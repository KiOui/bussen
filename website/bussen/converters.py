from django.urls.converters import SlugConverter
from .models import BusGameModel


class GameConverter(SlugConverter):
    """Converter for Subscription model."""

    def to_python(self, value):
        """
        Cast slug to Game.

        :param value: the slug of the Game
        :return: a Game or ValueError
        """
        try:
            return BusGameModel.objects.get(slug=value)
        except BusGameModel.DoesNotExist:
            raise ValueError

    def to_url(self, obj):
        """
        Cast an object of Game to a string.

        :param obj: the Game object
        :return: the public key of the Subscription object in string format
        """
        return str(obj.slug)

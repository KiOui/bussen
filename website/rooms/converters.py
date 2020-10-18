from django.urls.converters import SlugConverter
from .models import Game


class GameConverter(SlugConverter):
    """Converter for Subscription model."""

    def to_python(self, value):
        """
        Cast slug to Game.

        :param value: the slug of the Game
        :return: a Game or ValueError
        """
        try:
            return Game.objects.get(slug=value)
        except Game.DoesNotExist:
            raise ValueError

    def to_url(self, obj):
        """
        Cast an object of Game to a string.

        :param obj: the Game object
        :return: the public key of the Subscription object in string format
        """
        return str(obj.slug)

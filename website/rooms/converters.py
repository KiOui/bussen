from django.urls.converters import IntConverter
from .models import Room


class RoomConverter(IntConverter):
    """Converter for Room model."""

    def to_python(self, value):
        """
        Cast int to Room.

        :param value: the id of the Room
        :return: a Room or ValueError
        """
        try:
            return Room.objects.get(id=value)
        except Room.DoesNotExist:
            raise ValueError

    def to_url(self, obj):
        """
        Cast an object of Room to an int.

        :param obj: the Room object
        :return: the public key of the Room object in int format
        """
        return obj.id

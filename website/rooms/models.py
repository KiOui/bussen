import json
import secrets

from asgiref.sync import async_to_sync
from channels.layers import get_channel_layer
from django.contrib.auth import get_user_model
from django.db import models
from django.urls import reverse
from django.utils import timezone
from django.contrib.contenttypes.fields import GenericForeignKey
from django.contrib.contenttypes.models import ContentType
from django.utils.text import slugify
from games.utils import games

User = get_user_model()


class RoomStateException(Exception):
    """Exception for room state."""

    pass


class NoRoomForGameException(Exception):
    """Exception for no room."""

    pass


class InvalidAmountOfPlayersException(Exception):
    """Exception for an invalid amount of players."""

    pass


class Room(models.Model):
    """Room model."""

    name = models.CharField(max_length=64, blank=False, null=False, unique=True)
    slug = models.SlugField(null=False, blank=False, unique=True, max_length=256)
    content_type = models.ForeignKey(ContentType, on_delete=models.SET_NULL, null=True, blank=True)
    object_id = models.PositiveIntegerField(blank=True, null=True)
    game = GenericForeignKey("content_type", "object_id")

    def __str__(self) -> str:
        """Cast this object to a string."""
        return self.name

    def remove_player(self, player):
        """Remove a player from this room, executes before removal of player."""
        if self.game is not None:
            if self.game.remove_player(player) is None:
                print("Redirecting group")
                self.redirect_group(reverse("rooms:redirect"))

    @property
    def players(self):
        """Get all players in this room."""
        return Player.objects.filter(room=self).order_by("cookie")

    def save(self, *args, **kwargs):
        """
        Save method for Room object.

        Creates a slug for the room
        :param args: arguments
        :param kwargs: keyword arguments
        :return: None
        """
        if self.slug is None or self.slug == "":
            new_slug = slugify(self.name)
            if Room.objects.filter(slug=new_slug).exists():
                return ValueError("A slug for this game already exists, please choose another name")
            self.slug = new_slug
        super(Room, self).save(*args, **kwargs)

    def redirect_group(self, route):
        """Redirect this room to a new page."""
        self.send_group_message(json.dumps({"type": "redirect", "url": route}))

    def send_group_message(self, message):
        """Send a group message to this room."""
        channel_layer = get_channel_layer()
        async_to_sync(channel_layer.group_send)(self.slug, {"type": "send_group_message", "text": message})

    def start_game(self, game):
        """
        Start a game.

        :param game: the type of game to start, defined in the games application
        :return: True if the game was started successfully, an Exception otherwise
        """
        if self.game is None:
            if game in games.get_games().keys():
                if (
                    games.get_games()[game].minimum_amount_of_players()
                    <= self.players.count()
                    <= games.get_games()[game].maximum_amount_of_players()
                ):
                    new_game = games.get_games()[game].objects.create()
                    self.game = new_game
                    self.save()
                    self.redirect_group(reverse(new_game.get_route()))
                    return True
                else:
                    raise InvalidAmountOfPlayersException("Invalid amount of players.")
            else:
                raise ValueError("Game {} is not installed.".format(game))
        else:
            raise RoomStateException("Room {} is already in game.".format(self))


class Player(models.Model):
    """Player model."""

    PLAYER_COOKIE_NAME = "player_id"

    cookie = models.CharField(max_length=64)
    name = models.CharField(max_length=32, blank=False, null=False)
    room = models.ForeignKey(Room, on_delete=models.SET_NULL, null=True, blank=False, default=None)
    last_interaction = models.DateTimeField(auto_now_add=True)

    @property
    def online(self):
        """Check if a player is online."""
        return self.last_interaction >= timezone.now() - timezone.timedelta(minutes=1)

    def __init__(self, *args, **kwargs):
        """Initialise class."""
        super().__init__(*args, **kwargs)
        self._room = self.room

    def notify_room(self):
        """Notify this room."""
        if self._room is not None:
            self._room.remove_player(self)

    def save(self, *args, **kwargs):
        """
        Save method for Player object.

        :param args: arguments
        :param kwargs: keyword arguments
        :return: None
        """
        # Check if changes have been done to the room itself
        if self._room != self.room:
            self.notify_room()
        super(Player, self).save(*args, **kwargs)

    def __str__(self):
        """Convert this object to a string."""
        return self.name

    def in_room(self):
        """
        Check if a player is in a room.

        :return: True if the player is in a room, False otherwise
        """
        return self.room is not None

    def interaction(self, save=True):
        """Update last interaction of player."""
        self.last_interaction = timezone.now()
        if save:
            self.save()

    def to_json(self):
        """Convert this object to json."""
        return json.dumps(self.to_dict())

    def to_dict(self):
        """Convert this object to dict."""
        return {
            "name": self.name,
            "online": self.online,
            "last_interaction": self.last_interaction.strftime("%Y-%m-%dT%H:%M:%S.%fZ"),
            "room": self.room.__str__(),
            "cookie": self.cookie,
        }

    @staticmethod
    def get_new_player(name):
        """
        Generate a new player object with a random cookie token.

        :param name: the name for the player
        :return: a new Player object
        """
        random_token = secrets.token_hex(32)
        player = Player.objects.create(cookie=random_token, name=name)
        return player

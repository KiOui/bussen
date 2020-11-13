from asgiref.sync import async_to_sync
from channels.generic.websocket import SyncConsumer
from channels.layers import get_channel_layer
import json
from rooms.services import get_player_from_cookie
from .models import Player
from games.services import decode_message


class RoomConsumer(SyncConsumer):
    """Room consumer."""

    def websocket_connect(self, event):
        """Connect websocket."""
        room_name = self.scope["url_route"]['kwargs'].get('room_name')
        player_id_cookie = self.scope["cookies"].get(Player.PLAYER_COOKIE_NAME, None)
        player = get_player_from_cookie(player_id_cookie)
        if player is None or player.room is None or player.room.slug != room_name:
            self.disconnect_connection()
        else:
            player.interaction()
            self.add_to_group(player)
            async_to_sync(self.channel_layer.group_send)(
                player.room.slug,
                {"type": "send_group_message", "text": json.dumps({"type": "refresh"})},
            )
            self.accept_connection()

    def websocket_disconnect(self, code):
        """Disconnect websocket."""
        player_id_cookie = self.scope["cookies"].get("player_id", None)
        player = get_player_from_cookie(player_id_cookie)
        player.interaction()

    def add_to_group(self, player):
        """Add a player to the correct group."""
        async_to_sync(self.channel_layer.group_add)(player.room.slug, self.channel_name)

    def remove_from_group(self, player):
        """Remove a player from the group."""
        async_to_sync(self.channel_layer.group_discard)(player.room.slug, self.channel_name)

    def websocket_receive(self, event):
        """Receive websocket."""
        player_id_cookie = self.scope["cookies"].get("player_id", None)
        player = get_player_from_cookie(player_id_cookie)
        message = decode_message(event)
        self.execute_message(message, player)

    def execute_message(self, message, player):
        """Execute a message send by a player."""
        if 'game' in message.keys() and message['game'] and player.room.game is not None:
            send_back = player.room.game.execute_message(message, player)
            if send_back:
                self.send({"type": "websocket.send", "text": send_back})
        elif 'type' in message.keys():
            if message['type'] == 'ping':
                player.interaction()
                self.send({"type": "websocket.send", "text": json.dumps({"type": "refresh"})})

    def send_group_message(self, event):
        """Send a group message."""
        self.send({"type": "websocket.send", "text": event["text"]})

    def accept_connection(self):
        """Accept the connection."""
        self.send({"type": "websocket.accept"})

    def disconnect_connection(self):
        """Disconnect the connection."""
        self.send({"type": "websocket.disconnect"})

    def send_error_and_disconnect(self, error_msg="An error occurred"):
        """Send an error message and disconnect."""
        self.send_error(error_msg=error_msg)
        self.send({"type": "websocket.disconnect"})

    def send_error(self, error_msg="An error occurred"):
        """Send an error message."""
        response = {"type": "error", "message": error_msg}
        self.send({"type": "websocket.send", "text": json.dumps(response)})

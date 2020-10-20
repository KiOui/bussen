from asgiref.sync import async_to_sync
from channels.generic.websocket import SyncConsumer
import json
from django.urls import reverse
from rooms.models import Game
from rooms.services import get_player_from_cookie, decode_message


class GroupConsumer(SyncConsumer):
    """General group consumer."""

    def websocket_connect(self, event):
        """Connect websocket."""
        player_id_cookie = self.scope["cookies"].get("player_id", None)
        player = get_player_from_cookie(player_id_cookie)
        player.set_online()
        self.add_to_group(player)
        self.accept_connection()

    def websocket_disconnect(self, code):
        """Disconnect websocket."""
        player_id_cookie = self.scope["cookies"].get("player_id", None)
        player = get_player_from_cookie(player_id_cookie)
        player.set_offline()
        self.remove_from_group(player)

    def add_to_group(self, player):
        """Add a player to the correct group."""
        async_to_sync(self.channel_layer.group_add)(self.get_group_name(player.current_game), self.channel_name)

    def remove_from_group(self, player):
        """Remove a player from the group."""
        async_to_sync(self.channel_layer.group_discard)(self.get_group_name(player.current_game), self.channel_name)

    def websocket_receive(self, event):
        """Receive websocket."""
        player_id_cookie = self.scope["cookies"].get("player_id", None)
        player = get_player_from_cookie(player_id_cookie)
        message = decode_message(event)
        self.execute_message(message, player)

    def execute_message(self, message, player):
        """Execute a message send by a player."""
        pass

    def send_group_message(self, event):
        """Send a group message."""
        self.send({"type": "websocket.send", "text": event["text"]})

    @staticmethod
    def get_group_name(game):
        """Get the group name."""
        return ""

    def accept_connection(self):
        """Accept the connection."""
        self.send({"type": "websocket.accept"})

    def send_error_and_disconnect(self, error_msg="An error occurred"):
        """Send an error message and disconnect."""
        self.send_error(error_msg=error_msg)
        self.send({"type": "websocket.disconnect"})

    def send_error(self, error_msg="An error occurred"):
        """Send an error message."""
        response = {"type": "error", "message": error_msg}
        self.send({"type": "websocket.send", "text": json.dumps(response)})


class GamePhase3Consumer(GroupConsumer):
    """Phase 3 consumer."""

    def execute_message(self, message, player):
        """Execute a message send by a player."""
        if "type" not in message.keys():
            return False
        elif message["type"] == "phase3_guess":
            hub_websocket_id = self.get_group_name(player.current_game)
            correct = player.current_game.phase3_guess(message["guess"], player)
            if correct is not None:
                if not correct:
                    async_to_sync(self.channel_layer.group_send)(
                        hub_websocket_id,
                        {
                            "type": "send_group_message",
                            "text": json.dumps(
                                {
                                    "type": "message",
                                    "color": "red",
                                    "message": f"{player} guessed incorrectly and must drink",
                                }
                            ),
                        },
                    )

            if player.current_game.phase == Game.PHASE_FINISHED:
                async_to_sync(self.channel_layer.group_send)(
                    hub_websocket_id, {"type": "send_group_message", "text": json.dumps({"type": "celebrate"})}
                )

                for player in player.current_game.ordered_players:
                    player.current_game = None
                    player.save()

            async_to_sync(self.channel_layer.group_send)(
                hub_websocket_id, {"type": "send_group_message", "text": json.dumps({"type": "refresh"})}
            )

    @staticmethod
    def get_group_name(game):
        """Get the group name."""
        return f"game_room_phase_3_{game.id}"

    def accept_connection(self):
        """Accept the connection."""
        self.send({"type": "websocket.accept"})


class GamePhase2Consumer(GroupConsumer):
    """Phase 2 consumer."""

    def execute_message(self, message, player):
        """Execute a message send by a player."""
        if "type" not in message.keys():
            return False
        elif message["type"] == "phase2_card":
            hub_websocket_id = self.get_group_name(player.current_game)
            if message["suit"] is not None and message["rank"] is not None:
                if player.current_game.add_card_to_pile(player, message["suit"], message["rank"]):
                    async_to_sync(self.channel_layer.group_send)(
                        hub_websocket_id, {"type": "send_group_message", "text": json.dumps({"type": "refresh"})}
                    )
        elif message["type"] == "phase2_call":
            removed, card_of_player = player.current_game.call_card(message["id"])
            if removed:
                hub_websocket_id = self.get_group_name(player.current_game)
                async_to_sync(self.channel_layer.group_send)(
                    hub_websocket_id, {"type": "send_group_message", "text": json.dumps({"type": "refresh"})}
                )
                async_to_sync(self.channel_layer.group_send)(
                    hub_websocket_id,
                    {
                        "type": "send_group_message",
                        "text": json.dumps(
                            {
                                "type": "message",
                                "color": "yellow",
                                "message": f"{card_of_player}'s card was not correct. {card_of_player} must drink.",
                            }
                        ),
                    },
                )
            else:
                hub_websocket_id = self.get_group_name(player.current_game)
                async_to_sync(self.channel_layer.group_send)(
                    hub_websocket_id,
                    {
                        "type": "send_group_message",
                        "text": json.dumps(
                            {
                                "type": "message",
                                "color": "yellow",
                                "message": f"{card_of_player}'s card was correct. {player} must drink.",
                            }
                        ),
                    },
                )
        elif message["type"] == "phase2_next_card":
            if message["index"] == player.current_game.current_card:
                player.current_game.set_next_pyramid_card()
                hub_websocket_id = self.get_group_name(player.current_game)
                async_to_sync(self.channel_layer.group_send)(
                    hub_websocket_id, {"type": "send_group_message", "text": json.dumps({"type": "refresh"})}
                )
                if player.current_game.phase != Game.PHASE_2:
                    hub_websocket_id = self.get_group_name(player.current_game)
                    async_to_sync(self.channel_layer.group_send)(
                        hub_websocket_id,
                        {
                            "type": "send_group_message",
                            "text": json.dumps(
                                {
                                    "type": "redirect",
                                    "url": reverse("rooms:game_room", kwargs={"game": player.current_game}),
                                }
                            ),
                        },
                    )

    @staticmethod
    def get_group_name(game):
        """Get the group name."""
        return f"game_room_phase_2_{game.id}"


class GamePhase1Consumer(GroupConsumer):
    """Phase 1 game consumer."""

    def handle_phase1_answer(self, player, value):
        """Handle a phase 1 question answer."""
        answer = player.current_game.handle_phase1_answer(player, value)
        if answer is not None:
            hub_websocket_id = self.get_group_name(player.current_game)
            if answer["group_drink"]:
                async_to_sync(self.channel_layer.group_send)(
                    hub_websocket_id,
                    {
                        "type": "send_group_message",
                        "text": json.dumps(
                            {
                                "type": "message",
                                "color": "yellow",
                                "message": f"{player} guessed correctly. Everyone must drink.",
                            }
                        ),
                    },
                )
            elif answer["drink"]:
                async_to_sync(self.channel_layer.group_send)(
                    hub_websocket_id,
                    {
                        "type": "send_group_message",
                        "text": json.dumps(
                            {
                                "type": "message",
                                "color": "red",
                                "message": f"{player} guessed incorrectly. They need to drink.",
                            }
                        ),
                    },
                )
            else:
                async_to_sync(self.channel_layer.group_send)(
                    hub_websocket_id,
                    {
                        "type": "send_group_message",
                        "text": json.dumps(
                            {"type": "message", "color": "green", "message": f"{player} guessed correctly."}
                        ),
                    },
                )
            async_to_sync(self.channel_layer.group_send)(
                hub_websocket_id, {"type": "send_group_message", "text": json.dumps({"type": "refresh"})}
            )

    def execute_message(self, message, player):
        """Execute a phase 1 message."""
        if "type" not in message.keys():
            return False
        elif message["type"] == "phase1_answer":
            self.handle_phase1_answer(player, message["value"])
            if player.current_game.phase != Game.PHASE_1:
                hub_websocket_id = self.get_group_name(player.current_game)
                async_to_sync(self.channel_layer.group_send)(
                    hub_websocket_id,
                    {
                        "type": "send_group_message",
                        "text": json.dumps(
                            {
                                "type": "redirect",
                                "url": reverse("rooms:game_room", kwargs={"game": player.current_game}),
                            }
                        ),
                    },
                )

    @staticmethod
    def get_group_name(game):
        """Get group name."""
        return f"game_room_phase_1_{game.id}"


class HubConsumer(GroupConsumer):
    """Hub consumer."""

    def websocket_connect(self, event):
        """Connect websocket."""
        player_id_cookie = self.scope["cookies"].get("player_id", None)
        player = get_player_from_cookie(player_id_cookie)
        player.set_online()
        self.add_to_group(player)
        self.accept_connection()
        self.send_amount_of_players(player.current_game)

    def websocket_disconnect(self, code):
        """Disconnect websocket."""
        player_id_cookie = self.scope["cookies"].get("player_id", None)
        player = get_player_from_cookie(player_id_cookie)
        player.set_offline()
        self.send_amount_of_players(player.current_game)
        self.remove_from_group(player)

    def websocket_receive(self, event):
        """Receive websocket."""
        player_id_cookie = self.scope["cookies"].get("player_id", None)
        player = get_player_from_cookie(player_id_cookie)
        message = decode_message(event)
        self.execute_message(message, player)
        self.send_amount_of_players(player.current_game)

    def execute_message(self, message, player):
        """Execute message."""
        if "type" not in message.keys():
            return False
        elif message["type"] == "start_game":
            if player.current_game.start_phase_1():
                self.redirect_group(player.current_game)
            else:
                self.send_error("Game can not be started")

    def redirect_group(self, game):
        """Redirect the group."""
        hub_websocket_id = self.get_group_name(game)
        async_to_sync(self.channel_layer.group_send)(
            hub_websocket_id,
            {
                "type": "send_group_message",
                "text": json.dumps(
                    {"type": "game_redirect", "url": reverse("rooms:game_room", kwargs={"game": game})}
                ),
            },
        )

    @staticmethod
    def get_group_name(game):
        """Get group name."""
        return f"game_hub_{game.id}"

    def send_amount_of_players(self, game):
        """Send the amount of players in the group to the group."""
        amount_of_players = game.get_amount_of_players()
        amount_of_online_players = game.get_amount_of_online_players()
        response_dict = {
            "type": "player_amount",
            "players": amount_of_players,
            "online_players": amount_of_online_players,
            "can_start": game.enough_players and game.phase == Game.PHASE_OPEN,
        }
        async_to_sync(self.channel_layer.group_send)(
            self.get_group_name(game), {"type": "send_group_message", "text": json.dumps(response_dict)}
        )

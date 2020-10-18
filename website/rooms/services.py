import rooms.models
import json


def get_player_from_request(request):
    """
    Get a player from a request.

    :param request: the request
    :return: a Player object if the request has a player, False otherwise
    """
    player_id = request.COOKIES.get(rooms.models.Player.PLAYER_COOKIE_NAME, None)
    return get_player_from_cookie(player_id)


def get_player_from_cookie(player_id):
    """
    Get a player from the player id.

    :param player_id: the player id
    :return: a Player object if the player id matches, None otherwise
    """
    if player_id is not None:
        try:
            player = rooms.models.Player.objects.get(cookie=player_id)
            return player
        except rooms.models.Player.DoesNotExist:
            return None

    return None


def decode_message(message):
    """Decode a message from json."""
    text = message.get("text", None)
    if text is not None:
        try:
            return json.loads(text)
        except json.JSONDecodeError:
            return {}
    else:
        return {}


def card_rank_to_int(rank):
    """Convert a card rank to an Integer."""
    if rank == "J":
        return 11
    elif rank == "Q":
        return 12
    elif rank == "K":
        return 13
    elif rank == "A":
        return 14
    else:
        return int(rank)

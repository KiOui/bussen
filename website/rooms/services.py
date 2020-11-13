from .models import Player


def get_player_from_request(request):
    """
    Get a player from a request.

    :param request: the request
    :return: a Player object if the request has a player, False otherwise
    """
    player_id = request.COOKIES.get(Player.PLAYER_COOKIE_NAME, None)
    return get_player_from_cookie(player_id)


def get_player_from_cookie(player_id: str):
    """
    Get a player from the player id.

    :param player_id: the player id
    :return: a Player object if the player id matches, None otherwise
    """
    if player_id is not None:
        try:
            player = Player.objects.get(cookie=player_id)
            return player
        except Player.DoesNotExist:
            return None

    return None

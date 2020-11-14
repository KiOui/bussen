from .models import Player, Room


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


def execute_data_minimisation(dry_run=False):
    """
    Remove all players that are offline and all rooms that only have offline players.

    :param dry_run: does not really remove data if True
    :return: list of objects removed
    """
    deleted_rooms = list()
    deleted_players = list()

    rooms = Room.objects.all()
    for room in rooms:
        delete = True
        for player in room.players:
            if player.online:
                delete = False
        if delete:
            deleted_rooms.append(room)

    players = Player.objects.all()
    players_in_deleted_rooms = Player.objects.filter(room__in=deleted_rooms)
    for player in players:
        if not player.online and (player.room is None or player in players_in_deleted_rooms):
            deleted_players.append(player)

    if not dry_run:
        for room in deleted_rooms:
            room.delete()
        for player in deleted_players:
            player.delete()

    return [deleted_rooms] + [deleted_players]

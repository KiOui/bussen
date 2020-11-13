from django import template

from bussen.models import BusGameModel, Player, Hand

register = template.Library()


@register.inclusion_tag("bussen/player_cards.html", takes_context=True)
def render_game_cards(context, player, refresh=False):
    """Render order footer."""
    return {"player": player, "request": context.get("request"), "refresh": refresh, "hand": Hand.get_hand(player, player.room.game)}


@register.inclusion_tag("bussen/pyramid_header.html", takes_context=True)
def render_pyramid_header(context, player, refresh=False):
    """Render pyramid header."""
    return {"player": player, "request": context.get("request"), "refresh": refresh, "room": player.room}


@register.inclusion_tag("bussen/card.html", takes_context=False)
def render_card(suit, rank):
    """Render order footer."""
    return {
        "suit": suit,
        "rank": rank,
    }


@register.inclusion_tag("bussen/pyramid.html", takes_context=True)
def render_pyramid(context, player: Player, refresh=False):
    """Render order footer."""
    return {
        "player": player,
        "request": context.get("request"),
        "refresh": refresh,
        "pyramid": player.room.game.game.pyramid.pyramid,
        "current_card": player.room.game.game.pyramid.current_card(),
        "cards_on_pyramid": [x for x in player.room.game.game.pyramid.cards_on_pyramid if x.owner != player],
        "room": player.room
    }


@register.inclusion_tag("bussen/bus.html", takes_context=True)
def render_bus(context, player, refresh=False):
    """Render order footer."""
    return {
        "player": player,
        "request": context.get("request"),
        "refresh": refresh,
        "bus": player.room.game.game.bus.bus,
        "current_card": player.room.game.game.bus.current_card(),
        "room": player.room,
    }


@register.inclusion_tag("bussen/hand.html", takes_context=True)
def render_player_hand(context, player, refresh=False):
    """Render player cards."""
    return {
        "player": player,
        "request": context.get("request"),
        "refresh": refresh,
        "hand": Hand.get_hand(player, player.room.game).hand.hand,
    }


@register.inclusion_tag("bussen/player_question.html", takes_context=True)
def render_player_question(context, player, refresh=False):
    """Render order footer."""
    if player.room.game.phase != BusGameModel.PHASE_1:
        return {
            "player": player,
            "request": context.get("request"),
            "refresh": refresh,
            "display": False,
        }
    elif player == player.room.game.current_player:
        return {
            "player": player,
            "request": context.get("request"),
            "refresh": refresh,
            "question": player.room.game.get_card_question(player)["question"],
            "answers": player.room.game.get_card_question(player)["answers"],
            "display": True,
        }
    else:
        return {
            "player": player,
            "request": context.get("request"),
            "refresh": refresh,
            "question": None,
            "answers": [],
            "display": True,
        }

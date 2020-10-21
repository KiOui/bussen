from django import template

from bussen.models import BusGameModel, Player

register = template.Library()


@register.inclusion_tag("bussen/player_cards.html", takes_context=True)
def render_game_cards(context, player, refresh=False):
    """Render order footer."""
    return {"player": player, "request": context.get("request"), "refresh": refresh}


@register.inclusion_tag("bussen/pyramid_header.html", takes_context=True)
def render_pyramid_header(context, player, refresh=False):
    """Render pyramid header."""
    return {"player": player, "request": context.get("request"), "refresh": refresh}


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
        "pyramid": player.current_game.game.pyramid.pyramid,
        "current_card": player.current_game.game.pyramid.current_card(),
        "cards_on_pyramid": [x for x in player.current_game.game.pyramid.cards_on_pyramid if x.owner != player],
    }


@register.inclusion_tag("bussen/bus.html", takes_context=True)
def render_bus(context, player, refresh=False):
    """Render order footer."""
    return {
        "player": player,
        "request": context.get("request"),
        "refresh": refresh,
        "bus": player.current_game.game.bus.bus,
        "current_card": player.current_game.game.bus.current_card(),
    }


@register.inclusion_tag("bussen/hand.html", takes_context=True)
def render_player_hand(context, player, refresh=False):
    """Render player cards."""
    return {
        "player": player,
        "request": context.get("request"),
        "refresh": refresh,
        "hand": player.current_hand.hand.hand,
    }


@register.inclusion_tag("bussen/player_question.html", takes_context=True)
def render_player_question(context, player, refresh=False):
    """Render order footer."""
    if player.current_game.phase != BusGameModel.PHASE_1:
        return {
            "player": player,
            "request": context.get("request"),
            "refresh": refresh,
            "display": False,
        }
    elif player == player.current_game.current_player:
        return {
            "player": player,
            "request": context.get("request"),
            "refresh": refresh,
            "question": player.get_card_question()["question"],
            "answers": player.get_card_question()["answers"],
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

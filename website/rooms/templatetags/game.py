from django import template


register = template.Library()


@register.inclusion_tag("rooms/player_cards.html", takes_context=True)
def render_game_cards(context, player, refresh=False):
    """Render order footer."""
    return {"player": player, "request": context.get("request"), "refresh": refresh}


@register.inclusion_tag("rooms/pyramid_header.html", takes_context=True)
def render_pyramid_header(context, player, refresh=False):
    """Render pyramid header."""
    return {"player": player, "request": context.get("request"), "refresh": refresh}


@register.inclusion_tag("rooms/card.html", takes_context=False)
def render_card(suit, rank):
    """Render order footer."""
    return {
        "suit": suit,
        "rank": rank,
    }


@register.inclusion_tag("rooms/pyramid.html", takes_context=True)
def render_pyramid(context, player, refresh=False):
    """Render order footer."""
    return {"player": player, "request": context.get("request"), "refresh": refresh}


@register.inclusion_tag("rooms/bus.html", takes_context=True)
def render_bus(context, player, refresh=False):
    """Render order footer."""
    return {"player": player, "request": context.get("request"), "refresh": refresh}


@register.inclusion_tag("rooms/hand.html", takes_context=True)
def render_player_hand(context, player, refresh=False):
    """Render player cards."""
    return {"player": player, "request": context.get("request"), "refresh": refresh}


@register.inclusion_tag("rooms/player_question.html", takes_context=True)
def render_player_question(context, player, refresh=False):
    """Render order footer."""
    if player == player.current_game.current_player_obj:
        return {
            "player": player,
            "request": context.get("request"),
            "refresh": refresh,
            "question": player.get_card_question()["question"],
            "answers": player.get_card_question()["answers"],
        }
    else:
        return {
            "player": player,
            "request": context.get("request"),
            "refresh": refresh,
            "question": None,
            "answers": [],
        }

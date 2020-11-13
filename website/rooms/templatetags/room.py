from django import template
from games.utils import games

register = template.Library()


@register.inclusion_tag("rooms/room.html", takes_context=True)
def render_room(context, room, refresh=False):
    """Render room widget."""
    return {"room": room, "request": context.get("request"), "refresh": refresh, "games": list(games.get_games())}

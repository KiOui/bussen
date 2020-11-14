from django.http import Http404, JsonResponse
from django.shortcuts import render, redirect
from django.template.loader import get_template
from django.views.generic import TemplateView
from .forms import RoomCreationForm, PlayerCreationForm
from .models import Room, Player, RoomStateException, InvalidAmountOfPlayersException
from .services import get_player_from_request
from .templatetags.room import render_room


class RoomRedirectView(TemplateView):
    """Room redirect view."""

    def get(self, request, **kwargs):
        """GET request for redirect view, redirect users to correct view."""
        player = get_player_from_request(request)
        if player is None:
            return redirect("rooms:create_user")
        elif player.room is None:
            return redirect("rooms:overview_room")
        elif player.room.game is not None:
            return player.room.game.get_redirect_route()
        else:
            return redirect("rooms:room", room=player.room)


class RoomOverviewView(TemplateView):
    """Room Overview view."""

    template_name = "rooms/room_overview.html"

    def get(self, request, **kwargs):
        """GET request for room overview view."""
        player = get_player_from_request(request)
        if player is None or player.room is not None:
            return redirect("rooms:redirect")

        rooms = Room.objects.all()
        return render(request, self.template_name, {"rooms": rooms})


class JoinRoomView(TemplateView):
    """Join room view."""

    def get(self, request, **kwargs):
        """GET request for join room view."""
        player = get_player_from_request(request)
        if player is None or player.room is not None:
            return redirect("rooms:redirect")

        room = kwargs.get("room")
        if room.game is not None:
            return redirect("rooms:redirect")
        player.room = room
        player.save()
        return redirect("rooms:room", room=room)


class LeaveRoomView(TemplateView):
    """Leave room view."""

    def get(self, request, **kwargs):
        """GET request for leave room view."""
        room = kwargs.get("room")
        player = get_player_from_request(request)
        if player is None or player.room != room:
            return redirect("rooms:redirect")

        player.room = None
        player.save()
        return redirect("rooms:redirect")


class RoomView(TemplateView):
    """Room view."""

    template_name = "rooms/room_page.html"

    def get(self, request, **kwargs):
        """GET request for room page."""
        room = kwargs.get("room")
        player = get_player_from_request(request)
        if player is None or player.room != room:
            return redirect("rooms:redirect")
        return render(request, self.template_name, {"room": room})


class RoomRefreshView(TemplateView):
    """Refresh the Room view."""

    template_name = "rooms/room.html"

    def post(self, request, **kwargs):
        """
        POST request for refreshing the room.

        :param request: the request
        :param kwargs: keyword arguments
        :return: The orders in the following JSON format:
            data: [room]
        """
        room = kwargs.get("room")
        player = get_player_from_request(request)
        if player is None or player.room != room:
            return Http404()

        room = get_template(self.template_name).render(render_room({"request": request}, room, refresh=True), request)
        return JsonResponse({"data": room})


class CreateRoomView(TemplateView):
    """Create room view."""

    template_name = "rooms/create_room.html"

    def get(self, request, **kwargs):
        """GET request for create room view."""
        player = get_player_from_request(request)
        if player is None or player.room is not None:
            return redirect("rooms:redirect")
        return render(request, self.template_name, {"form": RoomCreationForm()})

    def post(self, request, **kwargs):
        """POST request for create room view."""
        player = get_player_from_request(request)
        if player is None or player.room is not None:
            return redirect("rooms:redirect")

        form = RoomCreationForm(request.POST)
        if form.is_valid():
            room_name = form.cleaned_data.get("room_name")
            if Room.objects.filter(name=room_name).exists():
                return render(request, self.template_name, {"form": form, "error": True})
            else:
                room = Room.objects.create(name=room_name)
                player.room = room
                player.save()
                return redirect("rooms:room", room=room)
        else:
            return render(request, self.template_name, {"form": form})


class CreateUserView(TemplateView):
    """Create user view."""

    template_name = "rooms/create_user.html"

    def get(self, request, **kwargs):
        """GET request for create user view."""
        player = get_player_from_request(request)
        if player is not None:
            form = PlayerCreationForm(initial={"player_name": player.name})
        else:
            form = PlayerCreationForm()
        return render(request, self.template_name, {"form": form})

    def post(self, request, **kwargs):
        """POST request for create user view."""
        player = get_player_from_request(request)
        form = PlayerCreationForm(request.POST)
        if form.is_valid():
            if player is None:
                player = Player.get_new_player(form.cleaned_data.get("player_name"))
            else:
                player.name = form.cleaned_data.get("player_name")
                player.save()
            redirect_with_cookie = redirect("rooms:redirect")
            redirect_with_cookie.set_cookie(Player.PLAYER_COOKIE_NAME, player.cookie)
            return redirect_with_cookie
        else:
            return render(request, self.template_name, {"form": form})


class StartGameView(TemplateView):
    """Start a game."""

    def post(self, request, **kwargs):
        """Start a game, checks if there are enough players and if no game has already been started."""
        room = kwargs.get("room")
        player = get_player_from_request(request)
        if player is None or player.room != room:
            return JsonResponse({"error": True, "errormsg": "Not authorized"})

        game = request.POST.get("game", None)
        try:
            room.start_game(game)
            return JsonResponse({"error": False})
        except RoomStateException:
            return JsonResponse({"error": True, "errormsg": "Room state error, please refresh this page."})
        except InvalidAmountOfPlayersException as e:
            return JsonResponse({"error": True, "errormsg": str(e)})
        except ValueError as e:
            return JsonResponse({"error": True, "errormsg": "Unknown error occurred"})


class KickPlayerView(TemplateView):
    """Kick a player."""

    def post(self, request, **kwargs):
        """Kick a player."""
        room = kwargs.get("room")
        player = get_player_from_request(request)
        if player is None or player.room is None or player.room != room:
            return JsonResponse({"succeeded": False})

        player_to_kick_id = request.POST.get("player", None)
        if player_to_kick_id is not None:
            try:
                player_to_kick = Player.objects.get(id=player_to_kick_id, room=player.room)
                if not player_to_kick.online:
                    player_to_kick.room = None
                    player_to_kick.save()
                    return JsonResponse({"succeeded": True})
                else:
                    return JsonResponse({"succeeded": False})
            except Player.DoesNotExist:
                return JsonResponse({"succeeded": False})
        return JsonResponse({"succeeded": False})

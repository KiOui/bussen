from django.http import Http404, JsonResponse
from django.shortcuts import render, redirect
from django.template.loader import get_template
from django.views.generic import TemplateView
from .forms import GameCreationForm, PlayerCreationForm
from .models import BusGameModel, Player
from .services import get_player_from_request
from .templatetags.game import (
    render_game_cards,
    render_player_question,
    render_pyramid,
    render_player_hand,
    render_pyramid_header,
    render_bus,
)


class RedirectView(TemplateView):
    """Redirect players view."""

    @staticmethod
    def redirect_remove_cookie(redirect_namespace):
        """Redirect to a namespace and remove the Player Cookie."""
        redirect_namespace.delete_cookie(Player.PLAYER_COOKIE_NAME)
        return redirect_namespace

    def get(self, request, **kwargs):
        """
        Redirect player to correct game view.

        :param request: the request
        :param kwargs: keyword arguments
        :return: a redirect to a specific game hub or player page
        """
        player = get_player_from_request(request)
        if player is None:
            return self.redirect_remove_cookie(redirect("bussen:enter"))
        elif player.current_game is None:
            return redirect("bussen:enter")
        elif player.current_game.phase == BusGameModel.PHASE_OPEN:
            return redirect("bussen:game_hub", game=player.current_game)
        else:
            return redirect("bussen:game_room", game=player.current_game)


class EnterRoomView(TemplateView):
    """Enter room view."""

    template_name = "bussen/enter.html"

    def get(self, request, **kwargs):
        """
        GET request for EnterRoomView.

        :param request: the request
        :param kwargs: keyword arguments
        :return: a render of the enter page
        """
        player = get_player_from_request(request)
        if player is None or player.current_game is None:
            form = GameCreationForm()
            return render(request, self.template_name, {"game_creation_form": form})
        else:
            return redirect("bussen:redirect")

    def post(self, request, **kwargs):
        """
        POST request for EnterRoomView.

        :param request: the request
        :param kwargs: keyword arguments
        :return: a render of the enter page on error, a redirect to the game hub page otherwise
        """
        player = get_player_from_request(request)
        if player is None or player.current_game is None:
            form = GameCreationForm(request.POST)
            if form.is_valid():
                game, _ = BusGameModel.objects.get_or_create(name=form.cleaned_data.get("game_name"))
                if game.phase == BusGameModel.PHASE_FINISHED:
                    game.delete()
                    game = BusGameModel.objects.create(name=form.cleaned_data.get("game_name"))
                return redirect("bussen:game_hub", game=game)
            else:
                return render(request, self.template_name, {"game_creation_form": form})
        else:
            return redirect("bussen:redirect")


class GameHubView(TemplateView):
    """Game hub view."""

    template_name = "bussen/game_hub.html"

    def get(self, request, **kwargs):
        """
        GET request for GameHubView.

        :param request: the request
        :param kwargs: keyword arguments
        :return: a render of the game_hub page
        """
        game = kwargs.get("game")
        player = get_player_from_request(request)
        if game.phase != BusGameModel.PHASE_OPEN:
            return redirect("bussen:redirect")
        elif player is None:
            return redirect("bussen:create_player", game=game)
        elif player.current_game is None:
            if player.name in [x.name for x in Player.objects.filter(current_game=game)]:
                player.delete()
                return redirect("bussen:create_player", game=game)
            else:
                player.current_game = game
                player.save()
                return render(request, self.template_name, {"game": game})
        elif player.current_game == game and game.phase == BusGameModel.PHASE_OPEN:
            return render(request, self.template_name, {"game": game})
        else:
            return redirect("bussen:redirect")


class GameView(TemplateView):
    """Game redirect view."""

    def get(self, request, **kwargs):
        """
        Redirect to the view the player is supposed to be at.

        :param request: the request
        :param kwargs: keyword arguments
        :return: a redirect to a game view the player is supposed to be at
        """
        game = kwargs.get("game")
        player = get_player_from_request(request)

        if not player or player.current_game != game:
            return redirect("bussen:redirect")
        elif player.current_game.phase == BusGameModel.PHASE_OPEN:
            return redirect("bussen:game_hub", game=game)
        elif player.current_game.phase == BusGameModel.PHASE_1:
            return redirect("bussen:game_room_phase_1", game=game)
        elif player.current_game.phase == BusGameModel.PHASE_2:
            return redirect("bussen:game_room_phase_2", game=game)
        elif player.current_game.phase == BusGameModel.PHASE_3:
            return redirect("bussen:game_room_phase_3", game=game)
        elif player.current_game.phase == BusGameModel.PHASE_FINISHED:
            player.current_game = None
            player.save()
            return redirect("bussen:redirect")
        else:
            return redirect("bussen:redirect")


class GamePhase1View(TemplateView):
    """Game view."""

    template_name = "bussen/game_phase_1.html"

    def get(self, request, **kwargs):
        """
        GET request for GameView.

        :param request: the request
        :param kwargs: keyword arguments
        :return: a render of the game page
        """
        game = kwargs.get("game")
        player = get_player_from_request(request)

        if not player or player.current_game != game or game.phase != BusGameModel.PHASE_1:
            return redirect("bussen:game_room", game=game)
        else:
            return render(request, self.template_name, {"game": game, "player": player})


class GamePhase2View(TemplateView):
    """Game view."""

    template_name = "bussen/game_phase_2.html"

    def get(self, request, **kwargs):
        """
        GET request for GameView.

        :param request: the request
        :param kwargs: keyword arguments
        :return: a render of the game page
        """
        game = kwargs.get("game")
        player = get_player_from_request(request)

        if not player or player.current_game != game or game.phase != BusGameModel.PHASE_2:
            return redirect("bussen:game_room", game=game)
        else:
            return render(request, self.template_name, {"game": game, "player": player})


class GamePhase3View(TemplateView):
    """Game phase 3 view."""

    template_name = "bussen/game_phase_3.html"

    def get(self, request, **kwargs):
        """
        GET request for GameView.

        :param request: the request
        :param kwargs: keyword arguments
        :return: a render of the game page
        """
        game = kwargs.get("game")
        player = get_player_from_request(request)

        if not player or player.current_game != game or game.phase != BusGameModel.PHASE_3:
            return redirect("bussen:game_room", game=game)
        else:
            return render(request, self.template_name, {"game": game, "player": player})


class CreatePlayerView(TemplateView):
    """Create player view."""

    template_name = "bussen/create_player.html"

    def get(self, request, **kwargs):
        """
        GET request for CreatePlayerView.

        :param request: the request
        :param kwargs: keyword arguments
        :return: a render of the create_player page
        """
        game = kwargs.get("game")
        player = get_player_from_request(request)
        if (player is None or player.current_game == game) and game.phase == BusGameModel.PHASE_OPEN:
            form = PlayerCreationForm(game)
            return render(request, self.template_name, {"player_creation_form": form, "game": game})
        else:
            return redirect("bussen:redirect")

    def post(self, request, **kwargs):
        """
        GET request for CreatePlayerView.

        :param request: the request
        :param kwargs: keyword arguments
        :return: a render of the create_player page
        """
        game = kwargs.get("game")
        player = get_player_from_request(request)

        if player is None:
            form = PlayerCreationForm(game, request.POST)
            if form.is_valid():
                try:
                    player = Player.get_new_player(form.cleaned_data.get("player_name"), current_game=game)
                except ValueError as error:
                    # TODO: Implement too many players screen
                    raise error
                redirect_with_cookie = redirect("bussen:redirect")
                redirect_with_cookie.set_cookie(Player.PLAYER_COOKIE_NAME, player.cookie)
                return redirect_with_cookie
            else:
                return render(request, self.template_name, {"player_creation_form": form, "game": game})
        else:
            if player.current_game == game and game.phase == BusGameModel.PHASE_OPEN:
                form = PlayerCreationForm(game, request.POST)
                if form.is_valid():
                    player.name = form.cleaned_data.get("player_name")
                    player.save()
                    return redirect("bussen:redirect")
                else:
                    return render(request, self.template_name, {"player_creation_form": form, "game": game})

        return redirect("bussen:redirect")


class CardRefreshView(TemplateView):
    """Refresh the Player cards view."""

    template_name = "bussen/player_cards.html"

    def post(self, request, **kwargs):
        """
        POST request for refreshing the player cards.

        :param request: the request
        :param kwargs: keyword arguments
        :return: The orders in the following JSON format:
            data: [player cards html]
        """
        game = kwargs.get("game")
        player = get_player_from_request(request)
        if player is None or player.current_game != game:
            return Http404()

        cards = get_template(self.template_name).render(render_game_cards({"request": request}, player, refresh=True))
        return JsonResponse({"data": cards})


class QuestionRefreshView(TemplateView):
    """Refresh the Player question view."""

    template_name = "bussen/player_question.html"

    def post(self, request, **kwargs):
        """
        POST request for refreshing the player question.

        :param request: the request
        :param kwargs: keyword arguments
        :return: The orders in the following JSON format:
            data: [player question]
        """
        game = kwargs.get("game")
        player = get_player_from_request(request)
        if player is None or player.current_game != game:
            return Http404()

        question = get_template(self.template_name).render(
            render_player_question({"request": request}, player, refresh=True)
        )
        return JsonResponse({"data": question})


class PyramidRefreshView(TemplateView):
    """Refresh the Player pyramid view."""

    template_name = "bussen/pyramid.html"

    def post(self, request, **kwargs):
        """
        POST request for refreshing the player pyramid.

        :param request: the request
        :param kwargs: keyword arguments
        :return: The orders in the following JSON format:
            data: [player pyramid]
        """
        game = kwargs.get("game")
        player = get_player_from_request(request)
        if player is None or player.current_game != game or player.current_game.phase != BusGameModel.PHASE_2:
            return Http404()

        pyramid = get_template(self.template_name).render(render_pyramid({"request": request}, player, refresh=True))
        return JsonResponse({"data": pyramid})


class PlayerHandRefreshView(TemplateView):
    """Refresh the Player hand view."""

    template_name = "bussen/hand.html"

    def post(self, request, **kwargs):
        """
        POST request for refreshing the player hand.

        :param request: the request
        :param kwargs: keyword arguments
        :return: The orders in the following JSON format:
            data: [player hand]
        """
        game = kwargs.get("game")
        player = get_player_from_request(request)
        if player is None or player.current_game != game:
            return Http404()

        hand = get_template(self.template_name).render(render_player_hand({"request": request}, player, refresh=True))
        return JsonResponse({"data": hand})


class PyramidHeaderRefreshView(TemplateView):
    """Refresh the Pyramid header view."""

    template_name = "bussen/pyramid_header.html"

    def post(self, request, **kwargs):
        """
        POST request for refreshing the player hand.

        :param request: the request
        :param kwargs: keyword arguments
        :return: The orders in the following JSON format:
            data: [pyramid header]
        """
        game = kwargs.get("game")
        player = get_player_from_request(request)
        if player is None or player.current_game != game:
            return Http404()

        hand = get_template(self.template_name).render(
            render_pyramid_header({"request": request}, player, refresh=True)
        )
        return JsonResponse({"data": hand})


class BusRefreshView(TemplateView):
    """Refresh the bus view."""

    template_name = "bussen/bus.html"

    def post(self, request, **kwargs):
        """
        POST request for refreshing the player hand.

        :param request: the request
        :param kwargs: keyword arguments
        :return: The orders in the following JSON format:
            data: [pyramid header]
        """
        game = kwargs.get("game")
        player = get_player_from_request(request)
        if player is None or player.current_game != game:
            return Http404()

        bus = get_template(self.template_name).render(render_bus({"request": request}, player, refresh=True))
        return JsonResponse({"data": bus})

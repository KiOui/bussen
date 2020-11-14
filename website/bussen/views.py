from django.http import Http404, JsonResponse
from django.shortcuts import render, redirect
from django.template.loader import get_template
from django.views.generic import TemplateView
from .models import BusGameModel
from rooms.services import get_player_from_request
from .templatetags.game import (
    render_game_cards,
    render_player_question,
    render_pyramid,
    render_player_hand,
    render_pyramid_header,
    render_bus,
)


class RedirectView(TemplateView):
    """Game redirect view."""

    def get(self, request, **kwargs):
        """
        Redirect to the view the player is supposed to be at.

        :param request: the request
        :param kwargs: keyword arguments
        :return: a redirect to a game view the player is supposed to be at
        """
        player = get_player_from_request(request)

        if player is None or player.room is None or player.room.game is None:
            return redirect("rooms:redirect")
        elif player.room.game.phase == BusGameModel.PHASE_1:
            return redirect("bussen:game_room_phase_1", room=player.room)
        elif player.room.game.phase == BusGameModel.PHASE_2:
            return redirect("bussen:game_room_phase_2", room=player.room)
        elif player.room.game.phase == BusGameModel.PHASE_3:
            return redirect("bussen:game_room_phase_3", room=player.room)
        elif player.room.game.phase == BusGameModel.PHASE_FINISHED:
            player.room.game = None
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
        room = kwargs.get("room")
        player = get_player_from_request(request)

        if (
            player is None
            or player.room != room
            or room.game is None
            or type(room.game) != BusGameModel
            or room.game.phase != BusGameModel.PHASE_1
        ):
            return redirect("bussen:redirect")
        else:
            return render(request, self.template_name, {"game": room.game, "player": player})


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
        room = kwargs.get("room")
        player = get_player_from_request(request)

        if (
            player is None
            or player.room != room
            or room.game is None
            or type(room.game) != BusGameModel
            or room.game.phase != BusGameModel.PHASE_2
        ):
            return redirect("bussen:redirect")
        else:
            return render(request, self.template_name, {"game": room.game, "player": player})


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
        room = kwargs.get("room")
        player = get_player_from_request(request)

        if (
            player is None
            or player.room != room
            or room.game is None
            or type(room.game) != BusGameModel
            or room.game.phase != BusGameModel.PHASE_3
        ):
            return redirect("bussen:redirect")
        else:
            return render(request, self.template_name, {"game": room.game, "player": player})


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
        room = kwargs.get("room")
        player = get_player_from_request(request)
        if player is None or player.room != room or player.room.game is None or type(player.room.game) != BusGameModel:
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
        room = kwargs.get("room")
        player = get_player_from_request(request)
        if player is None or player.room != room or player.room.game is None or type(player.room.game) != BusGameModel:
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
        room = kwargs.get("room")
        player = get_player_from_request(request)
        if (
            player is None
            or player.room != room
            or room.game is None
            or type(room.game) != BusGameModel
            or room.game.phase != BusGameModel.PHASE_2
        ):
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
        room = kwargs.get("room")
        player = get_player_from_request(request)
        if player is None or player.room != room or room.game is None or type(room.game) != BusGameModel:
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
        room = kwargs.get("room")
        player = get_player_from_request(request)
        if (
            player is None
            or player.room != room
            or room.game is None
            or type(room.game) != BusGameModel
            or room.game.phase != BusGameModel.PHASE_2
        ):
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
        room = kwargs.get("room")
        player = get_player_from_request(request)
        if (
            player is None
            or player.room != room
            or room.game is None
            or type(room.game) != BusGameModel
            or room.game.phase != BusGameModel.PHASE_3
        ):
            return Http404()

        bus = get_template(self.template_name).render(render_bus({"request": request}, player, refresh=True))
        return JsonResponse({"data": bus})

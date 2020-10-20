from django.urls import path, register_converter
from rooms.views import (
    EnterRoomView,
    GameHubView,
    CreatePlayerView,
    GameView,
    RedirectView,
    CardRefreshView,
    QuestionRefreshView,
    PlayerHandRefreshView,
    PyramidRefreshView,
    PyramidHeaderRefreshView,
    BusRefreshView,
    GamePhase1View,
    GamePhase2View,
    GamePhase3View,
)
from .converters import GameConverter

register_converter(GameConverter, "game")

urlpatterns = [
    path("", EnterRoomView.as_view(), name="enter"),
    path("redirect", RedirectView.as_view(), name="redirect"),
    path("<game:game>/", GameHubView.as_view(), name="game_hub"),
    path("<game:game>/create_player/", CreatePlayerView.as_view(), name="create_player"),
    path("<game:game>/game-room", GameView.as_view(), name="game_room"),
    path("<game:game>/game-room/phase1", GamePhase1View.as_view(), name="game_room_phase_1"),
    path("<game:game>/game-room/phase2", GamePhase2View.as_view(), name="game_room_phase_2"),
    path("<game:game>/game-room/phase3", GamePhase3View.as_view(), name="game_room_phase_3"),
    path("<game:game>/cards", CardRefreshView.as_view(), name="game_player_cards"),
    path("<game:game>/question", QuestionRefreshView.as_view(), name="game_player_question"),
    path("<game:game>/pyramid", PyramidRefreshView.as_view(), name="game_pyramid"),
    path("<game:game>/hand", PlayerHandRefreshView.as_view(), name="game_player_hand"),
    path("<game:game>/pyramid-header", PyramidHeaderRefreshView.as_view(), name="game_pyramid_header"),
    path("<game:game>/bus", BusRefreshView.as_view(), name="game_bus"),
]

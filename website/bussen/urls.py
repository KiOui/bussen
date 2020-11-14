from django.urls import path, register_converter
from bussen.views import (
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
from rooms.converters import RoomConverter

register_converter(RoomConverter, "room")

urlpatterns = [
    path("redirect", RedirectView.as_view(), name="redirect"),
    path("<room:room>/game-room/phase1", GamePhase1View.as_view(), name="game_room_phase_1"),
    path("<room:room>/game-room/phase2", GamePhase2View.as_view(), name="game_room_phase_2"),
    path("<room:room>/game-room/phase3", GamePhase3View.as_view(), name="game_room_phase_3"),
    path("<room:room>/cards", CardRefreshView.as_view(), name="game_player_cards"),
    path("<room:room>/question", QuestionRefreshView.as_view(), name="game_player_question"),
    path("<room:room>/pyramid", PyramidRefreshView.as_view(), name="game_pyramid"),
    path("<room:room>/hand", PlayerHandRefreshView.as_view(), name="game_player_hand"),
    path("<room:room>/pyramid-header", PyramidHeaderRefreshView.as_view(), name="game_pyramid_header"),
    path("<room:room>/bus", BusRefreshView.as_view(), name="game_bus"),
]

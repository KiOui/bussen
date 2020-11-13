from django.urls import path, register_converter
from .converters import RoomConverter
from .views import RoomView, CreateRoomView, CreateUserView, RoomRedirectView, RoomOverviewView, JoinRoomView, LeaveRoomView, StartGameView, RoomRefreshView, KickPlayerView

register_converter(RoomConverter, "room")

urlpatterns = [
    path("", RoomOverviewView.as_view(), name="overview_room"),
    path("<room:room>", RoomView.as_view(), name="room"),
    path("<room:room>/refresh", RoomRefreshView.as_view(), name="room_refresh"),
    path("create", CreateRoomView.as_view(), name="create_room"),
    path("set-username", CreateUserView.as_view(), name="create_user"),
    path("redirect", RoomRedirectView.as_view(), name="redirect"),
    path("<room:room>/join", JoinRoomView.as_view(), name="join_room"),
    path("<room:room>/leave", LeaveRoomView.as_view(), name="leave_room"),
    path("<room:room>/start-game", StartGameView.as_view(), name="start_game"),
    path("<room:room>/kick", KickPlayerView.as_view(), name="kick_player"),
]

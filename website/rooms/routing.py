from django.urls import re_path

from . import consumers

websocket_urlpatterns = [
    re_path(r"hubs/(?P<game_name>\w+)/$", consumers.HubConsumer),
    re_path(r"rooms/phase1/(?P<game_name>\w+)/$", consumers.GamePhase1Consumer),
    re_path(r"rooms/phase2/(?P<game_name>\w+)/$", consumers.GamePhase2Consumer),
    re_path(r"rooms/phase3/(?P<game_name>\w+)/$", consumers.GamePhase3Consumer),
]

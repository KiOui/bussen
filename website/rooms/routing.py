from django.conf.urls import url

from . import consumers

websocket_urlpatterns = [
    url(r"rooms/(?P<room_name>\w+)/$", consumers.RoomConsumer),
]

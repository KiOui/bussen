from channels.auth import AuthMiddlewareStack
from channels.routing import ProtocolTypeRouter, URLRouter
import rooms.routing as rooms

urlpatterns = list()
urlpatterns += rooms.websocket_urlpatterns

application = ProtocolTypeRouter(
    {
        # (http->django views is added by default)
        "websocket": AuthMiddlewareStack(URLRouter(urlpatterns)),
    }
)

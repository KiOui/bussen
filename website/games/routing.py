from channels.auth import AuthMiddlewareStack
from channels.routing import ProtocolTypeRouter, URLRouter
from channels.security.websocket import AllowedHostsOriginValidator
import rooms.routing as rooms

urlpatterns = list()
urlpatterns += rooms.websocket_urlpatterns

application = ProtocolTypeRouter(
    {
        # (http->django views is added by default)
        "websocket": AllowedHostsOriginValidator(AuthMiddlewareStack(URLRouter(urlpatterns)),),
    }
)

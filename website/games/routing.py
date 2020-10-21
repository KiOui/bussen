from channels.auth import AuthMiddlewareStack
from channels.routing import ProtocolTypeRouter, URLRouter
from channels.security.websocket import AllowedHostsOriginValidator
import bussen.routing as bussen

application = ProtocolTypeRouter(
    {
        # (http->django views is added by default)
        "websocket": AllowedHostsOriginValidator(AuthMiddlewareStack(URLRouter(bussen.websocket_urlpatterns)),),
    }
)

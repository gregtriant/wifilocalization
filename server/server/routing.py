from channels.auth import AuthMiddlewareStack
from channels.routing import ProtocolTypeRouter, URLRouter
from channels.security.websocket import OriginValidator
from channels.security.websocket import AllowedHostsOriginValidator
from django.urls import path
import wifirooms.routing

application = ProtocolTypeRouter({
    # 'websocket': OriginValidator(
    #     AuthMiddlewareStack(
    #         URLRouter(wifirooms.routing.ws_urlpatterns)
    #     ),
    #     ["*"]
    # ),
    "websocket": AllowedHostsOriginValidator(
        AuthMiddlewareStack(
            URLRouter(wifirooms.routing.ws_urlpatterns)
        ),
    ),
})

from django.urls import path
from .consumers import BrowserConsumer

ws_urlpatterns = [
    path('ws/browserWS/', BrowserConsumer.as_asgi()),
]

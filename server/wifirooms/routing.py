from django.urls import path
from .consumers import BrowserConsumer

ws_urlpatterns = [
    path('ws/graph/', BrowserConsumer.as_asgi()),
]

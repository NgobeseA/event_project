from django.urls import re_path
from .consumers import EventStatusConsumer

websocket_urlpatterns = [
    re_path(r'ws/events/$', EventStatusConsumer.as_asgi()),
]
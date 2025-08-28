"""
ASGI config for event_project project.

It exposes the ASGI callable as a module-level variable named ``application``.

For more information on this file, see
https://docs.djangoproject.com/en/5.2/howto/deployment/asgi/
"""

import os

from django.core.asgi import get_asgi_application

from channels.routing import ProtocolTypeRouter, URLRouter
from channels.auth import AuthMiddlewareStack
import events_app.routing

os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'event_project.settings')

application = get_asgi_application()
application = ProtocolTypeRouter({
    'websocket': AuthMiddlewareStack(
        URLRouter(events_app.routing.websocket_urlpatterns)
    ),
})

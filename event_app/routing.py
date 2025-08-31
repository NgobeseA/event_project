from django.urls import re_path
from .consumers import EventStatusConsumer, AdminNotificationConsumer, NotificationConsumer

websocket_urlpatterns = [
    #re_path(r'ws/events/$', EventStatusConsumer.as_asgi()),
    #re_path(r'ws/admin/nofications/$', AdminNotificationConsumer.as_asgi()),
    re_path(r'ws/notifications/',NotificationConsumer.as_asgi()),
    
]
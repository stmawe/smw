"""
ASGI config for smw project with Django Channels support.
"""

import os
from django.core.asgi import get_asgi_application
from channels.routing import ProtocolTypeRouter, URLRouter
from channels.auth import AuthMiddlewareStack
from channels.security.websocket import AllowedHostsOriginValidator

os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'config.settings.dev')

# Get Django ASGI application
django_asgi_app = get_asgi_application()

# Import after Django setup
from mydak.consumers import ChatConsumer
from django.urls import path

# WebSocket routes
ws_urlpatterns = [
    path('ws/chat/<int:conversation_id>/', ChatConsumer.as_asgi()),
]

application = ProtocolTypeRouter({
    'http': django_asgi_app,
    'websocket': AllowedHostsOriginValidator(
        AuthMiddlewareStack(
            URLRouter(
                ws_urlpatterns
            )
        )
    ),
})

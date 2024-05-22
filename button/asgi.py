"""
ASGI config for button project.

It exposes the ASGI callable as a module-level variable named ``application``.

For more information on this file, see
https://docs.djangoproject.com/en/4.2/howto/deployment/asgi/
"""

import os

from django.core.asgi import get_asgi_application
import button.routing  # 웹소켓 라우팅 파일

os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'button.settings')

from channels.routing import ProtocolTypeRouter, URLRouter
from channels.auth import AuthMiddlewareStack
import button.routing

# application = get_asgi_application()
application = ProtocolTypeRouter({
    "http": get_asgi_application(),
    'websocket': AuthMiddlewareStack(
        URLRouter(
            button.routing.websocket_urlpatterns  # 웹소켓 라우팅
        )
    ),
})

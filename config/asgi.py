# config/asgi.py
"""
Sesi\u00f3n 07 \u2014 Configuraci\u00f3n ASGI con Django Channels.

ProtocolTypeRouter enruta seg\u00fan el protocolo:
  - HTTP  \u2192 Django normal (get_asgi_application)
  - WS    \u2192 AuthMiddlewareStack \u2192 URLRouter con rutas de channels
"""
import os
import django

os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'config.settings')
django.setup()

from django.core.asgi import get_asgi_application
from channels.routing import ProtocolTypeRouter, URLRouter
from channels.auth import AuthMiddlewareStack
from channels.security.websocket import AllowedHostsOriginValidator
import envios.routing

application = ProtocolTypeRouter({
    # Peticiones HTTP normales \u2192 Django WSGI app
    'http': get_asgi_application(),

    # Conexiones WebSocket \u2192 Autenticaci\u00f3n \u2192 Rutas de channels
    'websocket': AllowedHostsOriginValidator(
        AuthMiddlewareStack(
            URLRouter(envios.routing.websocket_urlpatterns)
        )
    ),
})

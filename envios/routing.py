# envios/routing.py
"""
Sesi\u00f3n 07 \u2014 Rutas WebSocket del sistema de encomiendas.

Mapa de URLs WebSocket:
  ws/dashboard/           \u2192 DashboardConsumer  (stats en tiempo real)
  ws/encomienda/<pk>/     \u2192 EncomiendaConsumer  (detalle de una encomienda)
  ws/feed/                \u2192 ActivityFeedConsumer (feed global de actividad)
"""
from django.urls import re_path
from envios import consumers

websocket_urlpatterns = [
    # Dashboard live \u2014 contadores que se actualizan solos
    re_path(r'ws/dashboard/$', consumers.DashboardConsumer.as_asgi()),

    # Detalle de encomienda en tiempo real
    re_path(r'ws/encomienda/(?P<pk>\d+)/$', consumers.EncomiendaConsumer.as_asgi()),

    # Feed global de actividad del sistema
    re_path(r'ws/feed/$', consumers.ActivityFeedConsumer.as_asgi()),
]

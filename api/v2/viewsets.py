# api/v2/viewsets.py
"""
ViewSet para API v2 — versión simplificada.

Usa EncomiendaV2Serializer con campos reducidos y campo 'resumen'.
"""
from rest_framework import viewsets
from rest_framework.permissions import IsAuthenticated

from envios.models import Encomienda
from envios.serializers import EncomiendaV2Serializer
from api.permissions import EsEmpleadoActivo
from api.throttles import EmpleadoRateThrottle
from api.pagination import EncomiendaPagination


class EncomiendaV2ViewSet(viewsets.ReadOnlyModelViewSet):
    """
    API v2: Solo lectura (list + retrieve).
    Respuesta simplificada con campo 'resumen'.

    GET /api/v2/encomiendas/       → lista
    GET /api/v2/encomiendas/{pk}/  → detalle
    """
    queryset           = Encomienda.objects.con_relaciones()
    serializer_class   = EncomiendaV2Serializer
    permission_classes = [IsAuthenticated, EsEmpleadoActivo]
    throttle_classes   = [EmpleadoRateThrottle]
    pagination_class   = EncomiendaPagination
    ordering           = ['-fecha_registro']

# envios/viewsets.py
"""
ViewSets del sistema de encomiendas.

EncomiendaViewSet implementa el CRUD completo + acciones personalizadas:
    - cambiar_estado : POST /encomiendas/{pk}/cambiar_estado/
    - con_retraso    : GET  /encomiendas/con_retraso/
    - pendientes     : GET  /encomiendas/pendientes/
    - estadisticas   : GET  /encomiendas/estadisticas/
    - historial      : GET  /encomiendas/{pk}/historial/
"""
from rest_framework import viewsets, status
from rest_framework.decorators import action
from rest_framework.permissions import IsAuthenticated
from rest_framework.response import Response
from rest_framework.filters import SearchFilter, OrderingFilter
from django_filters.rest_framework import DjangoFilterBackend
from drf_spectacular.utils import extend_schema, OpenApiParameter

from .models import Encomienda, Empleado
from .serializers import (
    EncomiendaSerializer,
    EncomiendaDetailSerializer,
    HistorialEstadoSerializer,
)
from config.choices import EstadoEnvio
from api.filters import EncomiendaFilter
from api.pagination import EncomiendaPagination, HistorialPagination


class EncomiendaViewSet(viewsets.ModelViewSet):
    """
    ViewSet completo para encomiendas.

    ModelViewSet genera automáticamente:
        list()          → GET    /encomiendas/
        create()        → POST   /encomiendas/
        retrieve()      → GET    /encomiendas/{pk}/
        update()        → PUT    /encomiendas/{pk}/
        partial_update()→ PATCH  /encomiendas/{pk}/
        destroy()       → DELETE /encomiendas/{pk}/
    """
    queryset           = Encomienda.objects.con_relaciones()
    serializer_class   = EncomiendaSerializer
    permission_classes = [IsAuthenticated]
    pagination_class   = EncomiendaPagination

    # ── Filtros y búsqueda ────────────────────────────────────────
    filter_backends  = [DjangoFilterBackend, SearchFilter, OrderingFilter]
    filterset_class  = EncomiendaFilter
    search_fields    = [
        'codigo',
        'remitente__apellidos',
        'destinatario__apellidos',
        'descripcion',
    ]
    ordering_fields  = ['fecha_registro', 'peso_kg', 'costo_envio']
    ordering         = ['-fecha_registro']   # orden por defecto

    # ── Serializer dinámico según acción ──────────────────────────

    def get_serializer_class(self):
        """Usa EncomiendaDetailSerializer para el detalle individual."""
        if self.action == 'retrieve':
            return EncomiendaDetailSerializer
        return EncomiendaSerializer

    # ── Hook de creación ─────────────────────────────────────────

    def perform_create(self, serializer):
        """Asigna automáticamente el empleado del usuario autenticado."""
        try:
            empleado = Empleado.objects.get(email=self.request.user.email)
        except Empleado.DoesNotExist:
            empleado = Empleado.objects.first()  # fallback para pruebas
        serializer.save(empleado_registro=empleado)

    # ── Acción personalizada: cambiar estado ──────────────────────

    @extend_schema(
        summary='Cambiar estado de una encomienda',
        description='Cambia el estado de la encomienda y registra el cambio en el historial.',
        request={'application/json': {
            'type': 'object',
            'properties': {
                'estado':      {'type': 'string', 'example': 'TR'},
                'observacion': {'type': 'string', 'example': 'En camino a destino'},
            },
            'required': ['estado'],
        }},
        tags=['Encomiendas'],
    )
    @action(detail=True, methods=['post'], url_path='cambiar_estado')
    def cambiar_estado(self, request, pk=None):
        """
        POST /api/v1/encomiendas/{pk}/cambiar_estado/
        Body: {"estado": "TR", "observacion": "..."}
        """
        enc          = self.get_object()
        nuevo_estado = request.data.get('estado')
        observacion  = request.data.get('observacion', '')

        if not nuevo_estado:
            return Response(
                {'error': True, 'message': 'El campo estado es requerido.'},
                status=status.HTTP_400_BAD_REQUEST,
            )

        # Validar que el estado sea válido
        estados_validos = [e[0] for e in EstadoEnvio.choices]
        if nuevo_estado not in estados_validos:
            return Response(
                {
                    'error': True,
                    'message': f'Estado inválido. Opciones: {estados_validos}',
                },
                status=status.HTTP_400_BAD_REQUEST,
            )

        try:
            empleado = Empleado.objects.get(email=request.user.email)
        except Empleado.DoesNotExist:
            empleado = Empleado.objects.first()

        try:
            enc.cambiar_estado(nuevo_estado, empleado, observacion)
            return Response(EncomiendaSerializer(enc).data)
        except ValueError as e:
            return Response(
                {'error': True, 'message': str(e)},
                status=status.HTTP_400_BAD_REQUEST,
            )

    # ── Acción de lista: con retraso ──────────────────────────────

    @extend_schema(
        summary='Listar encomiendas con retraso',
        description='Retorna todas las encomiendas activas cuya fecha estimada ya pasó.',
        tags=['Encomiendas'],
    )
    @action(detail=False, methods=['get'], url_path='con_retraso')
    def con_retraso(self, request):
        """GET /api/v1/encomiendas/con_retraso/"""
        qs         = Encomienda.objects.con_retraso().con_relaciones()
        serializer = self.get_serializer(qs, many=True)
        return Response(serializer.data)

    # ── Acción de lista: pendientes ────────────────────────────────

    @extend_schema(
        summary='Listar encomiendas pendientes',
        description='Retorna todas las encomiendas en estado PENDIENTE.',
        tags=['Encomiendas'],
    )
    @action(detail=False, methods=['get'])
    def pendientes(self, request):
        """GET /api/v1/encomiendas/pendientes/"""
        qs         = Encomienda.objects.pendientes().con_relaciones()
        serializer = self.get_serializer(qs, many=True)
        return Response(serializer.data)

    # ── Acción de lista: estadísticas ─────────────────────────────

    @extend_schema(
        summary='Estadísticas del sistema',
        description='Retorna conteos y métricas agregadas de encomiendas.',
        tags=['Encomiendas'],
    )
    @action(detail=False, methods=['get'])
    def estadisticas(self, request):
        """GET /api/v1/encomiendas/estadisticas/"""
        from django.db.models import Count, Sum, Avg
        qs = Encomienda.objects

        stats = {
            'total':         qs.count(),
            'pendientes':    qs.pendientes().count(),
            'en_transito':   qs.en_transito().count(),
            'entregadas':    qs.entregadas().count(),
            'con_retraso':   qs.con_retraso().count(),
            'peso_promedio': qs.aggregate(avg=Avg('peso_kg'))['avg'],
            'costo_total':   qs.aggregate(total=Sum('costo_envio'))['total'],
        }
        return Response(stats)

    # ── Acción de detalle: historial ──────────────────────────────

    @extend_schema(
        summary='Historial de estados de una encomienda',
        description='Retorna todos los cambios de estado de una encomienda, paginados.',
        tags=['Encomiendas'],
    )
    @action(detail=True, methods=['get'])
    def historial(self, request, pk=None):
        """GET /api/v1/encomiendas/{pk}/historial/"""
        enc           = self.get_object()
        qs            = enc.historial.all().select_related('empleado')
        paginator     = HistorialPagination()
        page          = paginator.paginate_queryset(qs, request)
        serializer    = HistorialEstadoSerializer(page, many=True)
        return paginator.get_paginated_response(serializer.data)

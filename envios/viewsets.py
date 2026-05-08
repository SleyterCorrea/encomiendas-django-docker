# envios/viewsets.py
"""
ViewSets del sistema de encomiendas — Sesión 6 completa.

EncomiendaViewSet implementa:
    CRUD completo (ModelViewSet)
    Permisos: EsEmpleadoActivo + EsPropietarioOAdmin
    Throttling: EmpleadoRateThrottle + CambioEstadoThrottle
    Filtros, búsqueda, ordenamiento
    Paginación personalizada
    Cache Redis en estadisticas (15 min)
    Bulk operations: bulk_create y bulk_estado
    Acciones: cambiar_estado, con_retraso, pendientes, estadisticas, historial
"""
from rest_framework import viewsets, status
from rest_framework.decorators import action
from rest_framework.permissions import IsAuthenticated
from rest_framework.response import Response
from rest_framework.filters import SearchFilter, OrderingFilter
from django_filters.rest_framework import DjangoFilterBackend
from django.core.cache import cache
from django.db.models import Count, Sum, Avg
from drf_spectacular.utils import extend_schema

from .models import Encomienda, Empleado
from .serializers import (
    EncomiendaSerializer,
    EncomiendaDetailSerializer,
    HistorialEstadoSerializer,
)
from config.choices import EstadoEnvio
from api.filters import EncomiendaFilter
from api.pagination import EncomiendaPagination, HistorialPagination
from api.permissions import EsEmpleadoActivo, EsPropietarioOAdmin
from api.throttles import EmpleadoRateThrottle, CambioEstadoThrottle


class EncomiendaViewSet(viewsets.ModelViewSet):
    """
    ViewSet completo para encomiendas — Sesión 6.

    ModelViewSet genera:
        list()           → GET    /encomiendas/
        create()         → POST   /encomiendas/
        retrieve()       → GET    /encomiendas/{pk}/
        update()         → PUT    /encomiendas/{pk}/
        partial_update() → PATCH  /encomiendas/{pk}/
        destroy()        → DELETE /encomiendas/{pk}/
    """
    queryset           = Encomienda.objects.con_relaciones()
    serializer_class   = EncomiendaSerializer
    permission_classes = [IsAuthenticated, EsEmpleadoActivo, EsPropietarioOAdmin]
    throttle_classes   = [EmpleadoRateThrottle]
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
    ordering         = ['-fecha_registro']

    # ── Serializer dinámico según acción ─────────────────────────

    def get_serializer_class(self):
        if self.action == 'retrieve':
            return EncomiendaDetailSerializer
        return EncomiendaSerializer

    # ── to_representation personalizado: oculta campos según usuario

    def get_serializer(self, *args, **kwargs):
        """Pasa el request al context para que to_representation lo use."""
        kwargs.setdefault('context', {})
        kwargs['context']['request'] = self.request
        return super().get_serializer(*args, **kwargs)

    # ── Hook de creación ─────────────────────────────────────────

    def perform_create(self, serializer):
        try:
            empleado = Empleado.objects.get(email=self.request.user.email)
        except Empleado.DoesNotExist:
            empleado = Empleado.objects.first()
        serializer.save(empleado_registro=empleado)

    # ── Acción: cambiar estado ────────────────────────────────────

    @extend_schema(
        summary='Cambiar estado de una encomienda',
        tags=['Encomiendas'],
        request={'application/json': {
            'type': 'object',
            'properties': {
                'estado':      {'type': 'string', 'example': 'TR'},
                'observacion': {'type': 'string', 'example': 'En camino'},
            },
            'required': ['estado'],
        }},
    )
    @action(
        detail=True, methods=['post'], url_path='cambiar_estado',
        throttle_classes=[CambioEstadoThrottle],
    )
    def cambiar_estado(self, request, pk=None):
        """POST /api/v1/encomiendas/{pk}/cambiar_estado/"""
        enc          = self.get_object()
        nuevo_estado = request.data.get('estado')
        observacion  = request.data.get('observacion', '')

        if not nuevo_estado:
            return Response(
                {'error': True, 'message': 'El campo estado es requerido.'},
                status=status.HTTP_400_BAD_REQUEST,
            )
        estados_validos = [e[0] for e in EstadoEnvio.choices]
        if nuevo_estado not in estados_validos:
            return Response(
                {'error': True, 'message': f'Estado inválido. Opciones: {estados_validos}'},
                status=status.HTTP_400_BAD_REQUEST,
            )
        try:
            empleado = Empleado.objects.get(email=request.user.email)
        except Empleado.DoesNotExist:
            empleado = Empleado.objects.first()
        try:
            enc.cambiar_estado(nuevo_estado, empleado, observacion)
            # Invalidar cache de estadísticas al cambiar estado
            cache.delete('encomiendas:estadisticas')
            return Response(EncomiendaSerializer(enc).data)
        except ValueError as e:
            return Response(
                {'error': True, 'message': str(e)},
                status=status.HTTP_400_BAD_REQUEST,
            )

    # ── Acción: con retraso ───────────────────────────────────────

    @extend_schema(summary='Encomiendas con retraso', tags=['Encomiendas'])
    @action(detail=False, methods=['get'], url_path='con_retraso')
    def con_retraso(self, request):
        """GET /api/v1/encomiendas/con_retraso/"""
        qs = Encomienda.objects.con_retraso().con_relaciones()
        serializer = self.get_serializer(qs, many=True)
        return Response(serializer.data)

    # ── Acción: pendientes ────────────────────────────────────────

    @extend_schema(summary='Encomiendas pendientes', tags=['Encomiendas'])
    @action(detail=False, methods=['get'])
    def pendientes(self, request):
        """GET /api/v1/encomiendas/pendientes/"""
        qs = Encomienda.objects.pendientes().con_relaciones()
        serializer = self.get_serializer(qs, many=True)
        return Response(serializer.data)

    # ── Acción: estadísticas (con cache Redis 15 min) ─────────────

    @extend_schema(summary='Estadísticas del sistema', tags=['Encomiendas'])
    @action(detail=False, methods=['get'])
    def estadisticas(self, request):
        """
        GET /api/v1/encomiendas/estadisticas/
        Resultado cacheado 15 minutos en Redis.
        """
        cache_key = 'encomiendas:estadisticas'
        data = cache.get(cache_key)

        if data is None:
            qs   = Encomienda.objects
            data = {
                'total':         qs.count(),
                'pendientes':    qs.pendientes().count(),
                'en_transito':   qs.en_transito().count(),
                'entregadas':    qs.entregadas().count(),
                'con_retraso':   qs.con_retraso().count(),
                'peso_promedio': qs.aggregate(avg=Avg('peso_kg'))['avg'],
                'costo_total':   qs.aggregate(total=Sum('costo_envio'))['total'],
                'cached':        False,
            }
            cache.set(cache_key, data, 60 * 15)  # 15 minutos
        else:
            data['cached'] = True

        return Response(data)

    # ── Acción: historial paginado ────────────────────────────────

    @extend_schema(summary='Historial de estados', tags=['Encomiendas'])
    @action(detail=True, methods=['get'])
    def historial(self, request, pk=None):
        """GET /api/v1/encomiendas/{pk}/historial/"""
        enc       = self.get_object()
        qs        = enc.historial.all().select_related('empleado')
        paginator = HistorialPagination()
        page      = paginator.paginate_queryset(qs, request)
        return paginator.get_paginated_response(
            HistorialEstadoSerializer(page, many=True).data
        )

    # ── Acción: bulk_create ───────────────────────────────────────

    @extend_schema(
        summary='Crear múltiples encomiendas en una sola petición',
        tags=['Encomiendas'],
        request={'application/json': {
            'type': 'array',
            'items': {'type': 'object'},
        }},
    )
    @action(detail=False, methods=['post'], url_path='bulk_create')
    def bulk_create(self, request):
        """
        POST /api/v1/encomiendas/bulk_create/
        Body: lista de encomiendas
        """
        if not isinstance(request.data, list):
            return Response(
                {'error': True, 'message': 'Se esperaba una lista de encomiendas.'},
                status=status.HTTP_400_BAD_REQUEST,
            )

        try:
            empleado = Empleado.objects.get(email=request.user.email)
        except Empleado.DoesNotExist:
            empleado = Empleado.objects.first()

        serializer = EncomiendaSerializer(
            data=request.data, many=True, context={'request': request}
        )
        if serializer.is_valid():
            serializer.save(empleado_registro=empleado)
            return Response(serializer.data, status=status.HTTP_201_CREATED)
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)

    # ── Acción: bulk_estado ───────────────────────────────────────

    @extend_schema(
        summary='Cambiar estado de múltiples encomiendas',
        tags=['Encomiendas'],
        request={'application/json': {
            'type': 'object',
            'properties': {
                'ids':         {'type': 'array', 'items': {'type': 'integer'}},
                'estado':      {'type': 'string', 'example': 'TR'},
                'observacion': {'type': 'string'},
            },
            'required': ['ids', 'estado'],
        }},
    )
    @action(detail=False, methods=['patch'], url_path='bulk_estado')
    def bulk_estado(self, request):
        """
        PATCH /api/v1/encomiendas/bulk_estado/
        Body: {"ids": [1,2,3], "estado": "TR", "observacion": "..."}
        """
        ids          = request.data.get('ids', [])
        nuevo_estado = request.data.get('estado')
        observacion  = request.data.get('observacion', '')

        if not ids or not nuevo_estado:
            return Response(
                {'error': True, 'message': 'ids y estado son requeridos.'},
                status=status.HTTP_400_BAD_REQUEST,
            )

        estados_validos = [e[0] for e in EstadoEnvio.choices]
        if nuevo_estado not in estados_validos:
            return Response(
                {'error': True, 'message': f'Estado inválido: {estados_validos}'},
                status=status.HTTP_400_BAD_REQUEST,
            )

        try:
            empleado = Empleado.objects.get(email=request.user.email)
        except Empleado.DoesNotExist:
            empleado = Empleado.objects.first()

        encomiendas = Encomienda.objects.filter(id__in=ids)
        actualizadas, errores = [], []

        for enc in encomiendas:
            try:
                enc.cambiar_estado(nuevo_estado, empleado, observacion)
                actualizadas.append(enc.id)
            except ValueError as e:
                errores.append({'id': enc.id, 'error': str(e)})

        # Invalidar cache de estadísticas
        cache.delete('encomiendas:estadisticas')

        return Response({
            'actualizadas': actualizadas,
            'errores':      errores,
            'total':        len(actualizadas),
        })

# envios/api_views.py
"""
Vistas genéricas de DRF para clientes y rutas.

También incluye las vistas FBV (@api_view) y CBV (APIView + Mixins)
que se piden en los ítems 3, 4 y 5 del entregable de la Sesión 5.
"""
from rest_framework import generics, mixins, status
from rest_framework.views import APIView
from rest_framework.decorators import api_view, permission_classes
from rest_framework.permissions import IsAuthenticated
from rest_framework.response import Response
from django.shortcuts import get_object_or_404
from drf_spectacular.utils import extend_schema

from clientes.models import Cliente
from rutas.models import Ruta
from .models import Encomienda
from .serializers import (
    ClienteSerializer, RutaSerializer,
    EncomiendaSerializer, EncomiendaDetailSerializer,
)
from api.pagination import ClientePagination


# ─────────────────────────────────────────────────────────────────────────────
#  Item 3 del entregable: FBV con @api_view
# ─────────────────────────────────────────────────────────────────────────────

@extend_schema(tags=['Encomiendas'])
@api_view(['GET', 'POST'])
@permission_classes([IsAuthenticated])
def encomienda_list_fbv(request):
    """
    FBV - GET /api/v1/encomiendas-fbv/ → listar
         POST /api/v1/encomiendas-fbv/ → crear
    """
    if request.method == 'GET':
        qs         = Encomienda.objects.con_relaciones()
        serializer = EncomiendaSerializer(qs, many=True, context={'request': request})
        return Response(serializer.data)

    elif request.method == 'POST':
        serializer = EncomiendaSerializer(data=request.data, context={'request': request})
        if serializer.is_valid():
            from .models import Empleado
            try:
                empleado = Empleado.objects.get(email=request.user.email)
            except Empleado.DoesNotExist:
                empleado = Empleado.objects.first()
            serializer.save(empleado_registro=empleado)
            return Response(serializer.data, status=status.HTTP_201_CREATED)
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)


@extend_schema(tags=['Encomiendas'])
@api_view(['GET', 'PUT', 'PATCH', 'DELETE'])
@permission_classes([IsAuthenticated])
def encomienda_detail_fbv(request, pk):
    """
    FBV - GET /api/v1/encomiendas-fbv/{pk}/ → detalle
         PUT/PATCH → actualizar
         DELETE   → eliminar
    """
    enc = get_object_or_404(Encomienda, pk=pk)

    if request.method == 'GET':
        return Response(EncomiendaDetailSerializer(enc).data)

    elif request.method in ['PUT', 'PATCH']:
        s = EncomiendaSerializer(
            enc, data=request.data,
            partial=(request.method == 'PATCH'),
            context={'request': request},
        )
        if s.is_valid():
            s.save()
            return Response(s.data)
        return Response(s.errors, status=status.HTTP_400_BAD_REQUEST)

    elif request.method == 'DELETE':
        enc.delete()
        return Response(status=status.HTTP_204_NO_CONTENT)


# ─────────────────────────────────────────────────────────────────────────────
#  Item 4 del entregable: CBV con APIView
# ─────────────────────────────────────────────────────────────────────────────

class EncomiendaListAPIView(APIView):
    """CBV - GET /api/v1/encomiendas/ | POST /api/v1/encomiendas/"""
    permission_classes = [IsAuthenticated]

    def get(self, request):
        qs         = Encomienda.objects.con_relaciones()
        serializer = EncomiendaSerializer(qs, many=True, context={'request': request})
        return Response(serializer.data)

    def post(self, request):
        serializer = EncomiendaSerializer(data=request.data, context={'request': request})
        if serializer.is_valid():
            from .models import Empleado
            try:
                empleado = Empleado.objects.get(email=request.user.email)
            except Empleado.DoesNotExist:
                empleado = Empleado.objects.first()
            serializer.save(empleado_registro=empleado)
            return Response(serializer.data, status=status.HTTP_201_CREATED)
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)


class EncomiendaDetailAPIView(APIView):
    """CBV - GET/PUT/PATCH/DELETE /api/v1/encomiendas/{pk}/"""
    permission_classes = [IsAuthenticated]

    def get_object(self, pk):
        return get_object_or_404(Encomienda.objects.con_relaciones(), pk=pk)

    def get(self, request, pk):
        enc = self.get_object(pk)
        return Response(EncomiendaDetailSerializer(enc).data)

    def put(self, request, pk):
        enc = self.get_object(pk)
        s   = EncomiendaSerializer(enc, data=request.data, context={'request': request})
        if s.is_valid():
            s.save()
            return Response(s.data)
        return Response(s.errors, status=status.HTTP_400_BAD_REQUEST)

    def patch(self, request, pk):
        enc = self.get_object(pk)
        s   = EncomiendaSerializer(
            enc, data=request.data, partial=True, context={'request': request}
        )
        if s.is_valid():
            s.save()
            return Response(s.data)
        return Response(s.errors, status=status.HTTP_400_BAD_REQUEST)

    def delete(self, request, pk):
        enc = self.get_object(pk)
        enc.delete()
        return Response(status=status.HTTP_204_NO_CONTENT)


# ─────────────────────────────────────────────────────────────────────────────
#  Item 5 del entregable: Mixins combinados
# ─────────────────────────────────────────────────────────────────────────────

class EncomiendaListCreateView(
    mixins.ListModelMixin,
    mixins.CreateModelMixin,
    generics.GenericAPIView,
):
    """
    Mixin: List + Create
    GET  /api/v1/encomiendas-mixin/ → listar
    POST /api/v1/encomiendas-mixin/ → crear
    """
    queryset           = Encomienda.objects.con_relaciones()
    serializer_class   = EncomiendaSerializer
    permission_classes = [IsAuthenticated]

    def get(self, request, *args, **kwargs):
        return self.list(request, *args, **kwargs)

    def post(self, request, *args, **kwargs):
        return self.create(request, *args, **kwargs)

    def perform_create(self, serializer):
        """Hook: se llama antes de save() en create()"""
        from .models import Empleado
        try:
            empleado = Empleado.objects.get(email=self.request.user.email)
        except Empleado.DoesNotExist:
            empleado = Empleado.objects.first()
        serializer.save(empleado_registro=empleado)


class EncomiendaDetailMixinView(
    mixins.RetrieveModelMixin,
    mixins.UpdateModelMixin,
    mixins.DestroyModelMixin,
    generics.GenericAPIView,
):
    """
    Mixin: Retrieve + Update + Destroy
    GET    /api/v1/encomiendas-mixin/{pk}/ → detalle
    PUT    /api/v1/encomiendas-mixin/{pk}/ → actualizar
    PATCH  /api/v1/encomiendas-mixin/{pk}/ → actualizar parcial
    DELETE /api/v1/encomiendas-mixin/{pk}/ → eliminar
    """
    queryset           = Encomienda.objects.con_relaciones()
    serializer_class   = EncomiendaSerializer
    permission_classes = [IsAuthenticated]

    def get(self, request, *args, **kwargs):
        return self.retrieve(request, *args, **kwargs)

    def put(self, request, *args, **kwargs):
        return self.update(request, *args, **kwargs)

    def patch(self, request, *args, **kwargs):
        return self.partial_update(request, *args, **kwargs)

    def delete(self, request, *args, **kwargs):
        return self.destroy(request, *args, **kwargs)


# ─────────────────────────────────────────────────────────────────────────────
#  Item 6 del entregable: Generic Views (ListCreateAPIView, RetrieveUpdateDestroyAPIView)
# ─────────────────────────────────────────────────────────────────────────────

class ClienteListView(generics.ListAPIView):
    """
    Generic View para clientes activos.
    GET /api/v1/clientes/
    """
    serializer_class   = ClienteSerializer
    permission_classes = [IsAuthenticated]
    pagination_class   = ClientePagination

    def get_queryset(self):
        return Cliente.objects.activos()


class RutaListView(generics.ListAPIView):
    """
    Generic View para rutas activas.
    GET /api/v1/rutas/
    Las rutas son pocas: sin paginación.
    """
    serializer_class   = RutaSerializer
    permission_classes = [IsAuthenticated]
    pagination_class   = None  # Las rutas son pocas, no se pagina

    def get_queryset(self):
        return Ruta.objects.activas()

# api/permissions.py
"""
Permisos personalizados para la API de encomiendas.

EsEmpleadoActivo   → solo empleados con estado ACTIVO en la BD
EsPropietarioOAdmin → solo el empleado que creó la encomienda o un admin
"""
from rest_framework.permissions import BasePermission
from envios.models import Empleado
from config.choices import EstadoGeneral


class EsEmpleadoActivo(BasePermission):
    """
    Permite acceso solo a usuarios autenticados que tienen
    un Empleado asociado con estado ACTIVO.

    Uso en ViewSet:
        permission_classes = [IsAuthenticated, EsEmpleadoActivo]
    """
    message = 'Solo empleados activos pueden acceder a este recurso.'

    def has_permission(self, request, view):
        if not request.user or not request.user.is_authenticated:
            return False
        # Superusers siempre tienen acceso
        if request.user.is_superuser:
            return True
        # Verificar que tenga un empleado activo
        return Empleado.objects.filter(
            email=request.user.email,
            estado=EstadoGeneral.ACTIVO,
        ).exists()


class EsPropietarioOAdmin(BasePermission):
    """
    Permite:
    - Superusuarios: acceso total
    - Empleados admin/staff: acceso total
    - Empleados regulares: solo sus propias encomiendas (las que registraron)

    Uso como permiso de objeto en ViewSet:
        permission_classes = [IsAuthenticated, EsPropietarioOAdmin]
    """
    message = 'No tiene permiso para modificar este recurso.'

    def has_permission(self, request, view):
        return request.user and request.user.is_authenticated

    def has_object_permission(self, request, view, obj):
        # Superusuarios y staff: acceso total
        if request.user.is_superuser or request.user.is_staff:
            return True

        # Para métodos seguros (GET, HEAD, OPTIONS) todos pueden ver
        from rest_framework.permissions import SAFE_METHODS
        if request.method in SAFE_METHODS:
            return True

        # Para modificaciones: solo el empleado que registró la encomienda
        try:
            empleado = Empleado.objects.get(email=request.user.email)
            return obj.empleado_registro == empleado
        except Empleado.DoesNotExist:
            return False

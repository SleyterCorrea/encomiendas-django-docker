# api/throttles.py
"""
Throttles (limitadores de velocidad) personalizados para la API.

EmpleadoRateThrottle  → 100 peticiones/hora para empleados autenticados
LoginRateThrottle     → 5 intentos/minuto para el endpoint de login
"""
from rest_framework.throttling import UserRateThrottle, AnonRateThrottle


class EmpleadoRateThrottle(UserRateThrottle):
    """
    Limita las peticiones de empleados autenticados.
    Rate: 100 peticiones por hora.

    Uso en ViewSet:
        throttle_classes = [EmpleadoRateThrottle]
    """
    scope = 'empleado'


class LoginRateThrottle(AnonRateThrottle):
    """
    Limita los intentos de login (previene fuerza bruta).
    Rate: 5 peticiones por minuto para usuarios anónimos.

    Uso en la vista de login:
        throttle_classes = [LoginRateThrottle]
    """
    scope = 'login'


class CambioEstadoThrottle(UserRateThrottle):
    """
    Limita cambios de estado de encomiendas.
    Rate: 30 cambios por hora.
    """
    scope = 'cambio_estado'

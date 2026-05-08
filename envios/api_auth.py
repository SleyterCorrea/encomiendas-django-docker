# envios/api_auth.py
"""
Autenticación JWT personalizada para el sistema de encomiendas.

EncomiendaTokenSerializer  → agrega datos del empleado al payload del JWT
EncomiendaTokenView        → view que usa el serializer personalizado
LoginCookieView            → guarda tokens en cookies HttpOnly (más seguro)
LogoutCookieView           → elimina las cookies de sesión
"""
from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework import status
from rest_framework.permissions import AllowAny
from rest_framework_simplejwt.serializers import TokenObtainPairSerializer
from rest_framework_simplejwt.views import TokenObtainPairView
from rest_framework_simplejwt.tokens import RefreshToken
from drf_spectacular.utils import extend_schema


# ─────────────────────────────────────────────────────────────────────────────
#  JWT personalizado con datos del empleado
# ─────────────────────────────────────────────────────────────────────────────

class EncomiendaTokenSerializer(TokenObtainPairSerializer):
    """
    Extiende el JWT estándar agregando información del empleado al payload.
    El frontend puede decodificar el token y saber quién es el usuario
    sin hacer una petición adicional al servidor.
    """
    @classmethod
    def get_token(cls, user):
        token = super().get_token(user)

        # Datos básicos del usuario Django
        token['username'] = user.username
        token['email']    = user.email
        token['is_staff'] = user.is_staff

        # Datos del empleado relacionado (si existe)
        try:
            from envios.models import Empleado
            empleado = Empleado.objects.get(email=user.email)
            token['empleado_codigo']   = empleado.codigo
            token['empleado_cargo']    = empleado.cargo
            token['empleado_nombres']  = f'{empleado.nombres} {empleado.apellidos}'
        except Exception:
            # Usuario sin empleado relacionado (superuser, por ejemplo)
            token['empleado_codigo']  = None
            token['empleado_cargo']   = 'Administrador'
            token['empleado_nombres'] = user.get_full_name() or user.username

        return token


class EncomiendaTokenView(TokenObtainPairView):
    """
    POST /api/v1/auth/token/
    Devuelve access + refresh tokens con datos del empleado en el payload.
    """
    serializer_class = EncomiendaTokenSerializer


# ─────────────────────────────────────────────────────────────────────────────
#  Login / Logout con HttpOnly Cookies (más seguro contra XSS)
# ─────────────────────────────────────────────────────────────────────────────

@extend_schema(
    summary='Login con cookies HttpOnly',
    description='Autentica al usuario y guarda los tokens JWT en cookies HttpOnly seguras.',
    request={'application/json': {
        'type': 'object',
        'properties': {
            'username': {'type': 'string'},
            'password': {'type': 'string'},
        },
        'required': ['username', 'password'],
    }},
    tags=['Auth'],
)
class LoginCookieView(APIView):
    """
    POST /api/v1/auth/login/
    Autentica con usuario/contraseña y devuelve tokens en cookies HttpOnly.
    Más seguro que devolver el token en el body (protege contra XSS).
    """
    permission_classes = [AllowAny]

    def post(self, request):
        from django.contrib.auth import authenticate
        username = request.data.get('username')
        password = request.data.get('password')

        if not username or not password:
            return Response(
                {'error': True, 'message': 'username y password son requeridos.'},
                status=status.HTTP_400_BAD_REQUEST,
            )

        user = authenticate(username=username, password=password)
        if not user:
            return Response(
                {'error': True, 'message': 'Credenciales inválidas.'},
                status=status.HTTP_401_UNAUTHORIZED,
            )

        # Generar tokens con datos del empleado
        refresh = RefreshToken.for_user(user)
        # Agregar datos del empleado al token
        try:
            from envios.models import Empleado
            empleado = Empleado.objects.get(email=user.email)
            refresh['empleado_cargo']   = empleado.cargo
            refresh['empleado_codigo']  = empleado.codigo
            refresh['empleado_nombres'] = f'{empleado.nombres} {empleado.apellidos}'
        except Exception:
            refresh['empleado_cargo']   = 'Administrador'
            refresh['empleado_codigo']  = None
            refresh['empleado_nombres'] = user.get_full_name() or user.username

        response = Response({
            'message': 'Login exitoso.',
            'user': user.username,
        })

        # Guardar tokens en cookies HttpOnly
        response.set_cookie(
            key='access_token',
            value=str(refresh.access_token),
            httponly=True,          # no accesible desde JS
            secure=False,           # True en HTTPS/producción
            samesite='Lax',         # protege contra CSRF
            max_age=3600,           # 1 hora
        )
        response.set_cookie(
            key='refresh_token',
            value=str(refresh),
            httponly=True,
            secure=False,
            samesite='Lax',
            max_age=604800,         # 7 días
        )
        return response


@extend_schema(
    summary='Logout — elimina cookies de sesión',
    tags=['Auth'],
)
class LogoutCookieView(APIView):
    """
    POST /api/v1/auth/logout/
    Elimina las cookies de sesión JWT.
    """
    permission_classes = [AllowAny]

    def post(self, request):
        response = Response({'message': 'Logout exitoso.'})
        response.delete_cookie('access_token')
        response.delete_cookie('refresh_token')
        return response

from pathlib import Path
from datetime import timedelta
from decouple import config

BASE_DIR = Path(__file__).resolve().parent.parent

SECRET_KEY = config('SECRET_KEY', default='django-insecure-change-me')
DEBUG = config('DEBUG', cast=bool, default=False)
ALLOWED_HOSTS = [host.strip() for host in config('ALLOWED_HOSTS', default='localhost,127.0.0.1').split(',') if host.strip()]

INSTALLED_APPS = [
    'django.contrib.admin',
    'django.contrib.auth',
    'django.contrib.contenttypes',
    'django.contrib.sessions',
    'django.contrib.messages',
    'django.contrib.staticfiles',
    # Apps del proyecto
    'envios',
    'clientes',
    'rutas',
    # Django REST Framework
    'rest_framework',
    'rest_framework_simplejwt',
    'rest_framework_simplejwt.token_blacklist',
    'django_filters',
    'drf_spectacular',
    'corsheaders',
    # App API
    'api',
]

MIDDLEWARE = [
    'corsheaders.middleware.CorsMiddleware',  # <-- PRIMERO para CORS
    'django.middleware.security.SecurityMiddleware',
    'django.contrib.sessions.middleware.SessionMiddleware',
    'django.middleware.common.CommonMiddleware',
    'django.middleware.csrf.CsrfViewMiddleware',
    'django.contrib.auth.middleware.AuthenticationMiddleware',
    'django.contrib.messages.middleware.MessageMiddleware',
    'django.middleware.clickjacking.XFrameOptionsMiddleware',
]

ROOT_URLCONF = 'config.urls'

TEMPLATES = [
    {
        'BACKEND': 'django.template.backends.django.DjangoTemplates',
        'DIRS': [BASE_DIR / 'templates'],
        'APP_DIRS': True,
        'OPTIONS': {
            'context_processors': [
                'django.template.context_processors.debug',
                'django.template.context_processors.request',
                'django.contrib.auth.context_processors.auth',
                'django.contrib.messages.context_processors.messages',
            ],
        },
    },
]

WSGI_APPLICATION = 'config.wsgi.application'
ASGI_APPLICATION = 'config.asgi.application'

DB_ENGINE = config('DB_ENGINE', default='django.db.backends.sqlite3')
if DB_ENGINE == 'django.db.backends.sqlite3':
    DATABASES = {
        'default': {
            'ENGINE': DB_ENGINE,
            'NAME': BASE_DIR / config('SQLITE_NAME', default='db.sqlite3'),
        }
    }
else:
    DATABASES = {
        'default': {
            'ENGINE': DB_ENGINE,
            'NAME': config('DB_NAME'),
            'USER': config('DB_USER'),
            'PASSWORD': config('DB_PASSWORD'),
            'HOST': config('DB_HOST', default='db'),
            'PORT': config('DB_PORT', default='5432'),
        }
    }

AUTH_PASSWORD_VALIDATORS = [
    {'NAME': 'django.contrib.auth.password_validation.UserAttributeSimilarityValidator'},
    {'NAME': 'django.contrib.auth.password_validation.MinimumLengthValidator'},
    {'NAME': 'django.contrib.auth.password_validation.CommonPasswordValidator'},
    {'NAME': 'django.contrib.auth.password_validation.NumericPasswordValidator'},
]

LANGUAGE_CODE = 'es-pe'
TIME_ZONE = 'America/Lima'
USE_I18N = True
USE_TZ = True

STATIC_URL = 'static/'
STATIC_ROOT = BASE_DIR / 'staticfiles'
STATICFILES_DIRS = [BASE_DIR / 'static']
MEDIA_URL = '/media/'
MEDIA_ROOT = BASE_DIR / 'media'
DEFAULT_AUTO_FIELD = 'django.db.models.BigAutoField'

# ── Autenticación ────────────────────────────────────────
LOGIN_URL           = '/accounts/login/'
LOGIN_REDIRECT_URL  = '/'
LOGOUT_REDIRECT_URL = '/accounts/login/'

# ── Sesiones (8 horas de jornada laboral) ──────────────────
SESSION_ENGINE                = 'django.contrib.sessions.backends.db'
SESSION_EXPIRE_AT_BROWSER_CLOSE = False
SESSION_COOKIE_AGE            = 60 * 60 * 8  # 8 horas
SESSION_COOKIE_SECURE         = False         # True en producción
SESSION_COOKIE_NAME           = 'encomiendas_session'

# ── Django REST Framework ─────────────────────────────────────────
REST_FRAMEWORK = {
    # Autenticación: JWT por defecto para toda la API
    'DEFAULT_AUTHENTICATION_CLASSES': [
        'rest_framework_simplejwt.authentication.JWTAuthentication',
    ],
    # Permisos: requiere autenticación por defecto
    'DEFAULT_PERMISSION_CLASSES': [
        'rest_framework.permissions.IsAuthenticated',
    ],
    # Paginación: 15 registros por página
    'DEFAULT_PAGINATION_CLASS': 'rest_framework.pagination.PageNumberPagination',
    'PAGE_SIZE': 15,
    # Documentación automática con drf-spectacular
    'DEFAULT_SCHEMA_CLASS': 'drf_spectacular.openapi.AutoSchema',
    # Filtros: django-filter como backend por defecto
    'DEFAULT_FILTER_BACKENDS': [
        'django_filters.rest_framework.DjangoFilterBackend',
        'rest_framework.filters.SearchFilter',
        'rest_framework.filters.OrderingFilter',
    ],
    # Manejo de excepciones personalizado
    'EXCEPTION_HANDLER': 'api.exceptions.encomiendas_exception_handler',
}

# ── JWT: configuración de tokens ──────────────────────────────────
SIMPLE_JWT = {
    'ACCESS_TOKEN_LIFETIME':  timedelta(minutes=60),   # token expira en 1 hora
    'REFRESH_TOKEN_LIFETIME': timedelta(days=7),        # refresh expira en 7 días
    'ROTATE_REFRESH_TOKENS':  True,                     # rotar el refresh en cada uso
    'BLACKLIST_AFTER_ROTATION': True,
    'AUTH_HEADER_TYPES':      ('Bearer',),              # Authorization: Bearer <token>
    'USER_ID_FIELD':          'id',
    'USER_ID_CLAIM':          'user_id',
}

# ── CORS: permitir peticiones desde el frontend ───────────────────
CORS_ALLOW_ALL_ORIGINS = True  # en desarrollo
# En producción reemplazar por:
# CORS_ALLOWED_ORIGINS = ['https://tu-frontend.com']

# ── Documentación de la API (drf-spectacular) ─────────────────────
SPECTACULAR_SETTINGS = {
    'TITLE': 'API Sistema de Gestión de Encomiendas',
    'DESCRIPTION': '''
        API REST para gestionar el ciclo de vida de encomiendas.
        Incluye registro de envíos, cambio de estado, historial y estadísticas.

        **Cómo autenticarse:**
        1. Ejecuta POST /api/v1/auth/token/ con usuario y contraseña
        2. Copia el valor del campo "access"
        3. Haz clic en "Authorize" (arriba a la derecha)
        4. Pega SOLO el token (sin "Bearer ") en el campo y haz clic en Authorize
    ''',
    'VERSION': '1.0.0',
    'SERVE_INCLUDE_SCHEMA': False,
    'COMPONENT_SPLIT_REQUEST': True,
    'SORT_OPERATIONS': False,
    'TAGS': [
        {'name': 'Encomiendas', 'description': 'Gestión de envíos'},
        {'name': 'Clientes',    'description': 'Listado de clientes activos'},
        {'name': 'Rutas',       'description': 'Rutas disponibles'},
        {'name': 'Auth',        'description': 'Autenticación JWT'},
    ],
    # Swagger UI configuración
    'SWAGGER_UI_SETTINGS': {
        'persistAuthorization': True,   # mantiene el token entre recargas
        'deepLinking': True,            # links directos a endpoints
        'displayRequestDuration': True,  # muestra tiempo de respuesta
        'filter': True,                  # buscador de endpoints
    },
    # Esquema de seguridad JWT explícito para Swagger UI
    'SECURITY': [{'jwtAuth': []}],
}


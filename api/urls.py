# api/urls.py
"""
URLs de la API REST v1.
El router genera automáticamente los endpoints del ViewSet.
"""
from django.urls import path, include
from rest_framework.routers import DefaultRouter
from rest_framework_simplejwt.views import TokenRefreshView

from envios.viewsets import EncomiendaViewSet
from envios import api_views
from envios.api_auth import EncomiendaTokenView, LoginCookieView, LogoutCookieView

# ── Router: genera URLs automáticamente ─────────────────────────────
router = DefaultRouter()
router.register('encomiendas', EncomiendaViewSet, basename='encomienda')

urlpatterns = [
    # ── Endpoints generados por el Router (CRUD completo) ────────────
    path('', include(router.urls)),

    # ── Endpoints de clientes y rutas (Generic Views) ────────────────
    path('clientes/', api_views.ClienteListView.as_view(),  name='cliente-list'),
    path('rutas/',    api_views.RutaListView.as_view(),     name='ruta-list'),

    # ── Autenticación JWT ────────────────────────────────────────────
    path('auth/token/',         EncomiendaTokenView.as_view(),  name='token_obtain'),
    path('auth/token/refresh/', TokenRefreshView.as_view(),     name='token_refresh'),
    path('auth/login/',         LoginCookieView.as_view(),      name='login_cookie'),
    path('auth/logout/',        LogoutCookieView.as_view(),     name='logout_cookie'),
]

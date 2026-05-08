# config/urls.py
from django.contrib import admin
from django.urls import path, include
from django.conf import settings
from django.conf.urls.static import static
from drf_spectacular.views import (
    SpectacularAPIView,
    SpectacularSwaggerView,
    SpectacularRedocView,
)

urlpatterns = [
    path('admin/',    admin.site.urls),
    path('',          include('envios.urls')),
    path('accounts/', include('django.contrib.auth.urls')),  # login/logout incluidos

    # ── API REST v1 ──────────────────────────────────────────────
    path('api/v1/', include('api.urls')),

    # ── API REST v2 (simplificada, solo lectura) ──────────────────
    path('api/v2/', include('api.v2.urls')),

    # ── Documentación OpenAPI ────────────────────────────────────
    path('api/schema/', SpectacularAPIView.as_view(), name='schema'),
    path('api/docs/',   SpectacularSwaggerView.as_view(url_name='schema'), name='swagger'),
    path('api/redoc/',  SpectacularRedocView.as_view(url_name='schema'),   name='redoc'),
]

if settings.DEBUG:
    urlpatterns += static(settings.STATIC_URL, document_root=settings.STATIC_ROOT)
    urlpatterns += static(settings.MEDIA_URL,  document_root=settings.MEDIA_ROOT)


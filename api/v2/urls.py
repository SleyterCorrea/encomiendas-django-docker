# api/v2/urls.py
"""
URLs para la API v2 — versión simplificada con EncomiendaV2Serializer.

Diferencias con v1:
- Usa EncomiendaV2Serializer (menos campos, campo 'resumen', HyperlinkedField)
- Sin acciones bulk por defecto
- Documentado con el tag 'v2'
"""
from rest_framework.routers import DefaultRouter
from .viewsets import EncomiendaV2ViewSet

router = DefaultRouter()
router.register(r'encomiendas', EncomiendaV2ViewSet, basename='encomienda-v2')

urlpatterns = router.urls

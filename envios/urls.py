# envios/urls.py
from django.urls import path
from . import views

urlpatterns = [
    # Dashboard
    path('', views.dashboard, name='dashboard'),

    # Encomiendas — nombres exactos del PDF
    path('encomiendas/',                    views.encomienda_lista,          name='encomienda_lista'),
    path('encomiendas/nueva/',              views.encomienda_crear,          name='encomienda_crear'),
    path('encomiendas/<int:pk>/',           views.encomienda_detalle,        name='encomienda_detalle'),
    path('encomiendas/<int:pk>/estado/',    views.encomienda_cambiar_estado, name='encomienda_cambiar_estado'),
]

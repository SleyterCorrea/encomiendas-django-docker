# envios/urls.py
from django.urls import path
from . import views, views_auth

urlpatterns = [
    # ── Autenticación ─────────────────────────────────────
    path('accounts/login/',  views_auth.login_view,  name='login'),
    path('accounts/logout/', views_auth.logout_view, name='logout'),
    path('accounts/perfil/', views_auth.perfil_view, name='perfil'),

    # ── Dashboard ─────────────────────────────────────────
    path('', views.dashboard, name='dashboard'),

    # ── Encomiendas ───────────────────────────────────────
    path('encomiendas/',              views.lista_encomiendas,     name='lista'),
    path('encomiendas/crear/',        views.crear_encomienda,      name='crear'),
    path('encomiendas/<int:pk>/',     views.detalle_encomienda,    name='detalle'),
    path('encomiendas/<int:pk>/estado/', views.cambiar_estado_encomienda, name='cambiar_estado'),
]

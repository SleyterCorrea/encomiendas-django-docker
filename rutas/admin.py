from django.contrib import admin
from .models import Ruta


@admin.register(Ruta)
class RutaAdmin(admin.ModelAdmin):
    list_display = ('origen', 'destino', 'distancia_km', 'activa')
    list_filter = ('activa',)
    search_fields = ('origen', 'destino')

# api/filters.py
"""
Filtros personalizados para la API de encomiendas usando django-filter.
"""
from django_filters.rest_framework import (
    FilterSet, CharFilter, ChoiceFilter, BooleanFilter, DateFilter,
)
from django.utils import timezone
from envios.models import Encomienda
from config.choices import EstadoEnvio


class EncomiendaFilter(FilterSet):
    """
    Filtros disponibles para el endpoint /api/v1/encomiendas/

    Ejemplos de uso:
        GET /api/v1/encomiendas/?estado=TR
        GET /api/v1/encomiendas/?ruta=LIM-TRU
        GET /api/v1/encomiendas/?remitente=12345678
        GET /api/v1/encomiendas/?desde=2026-01-01&hasta=2026-04-30
        GET /api/v1/encomiendas/?con_retraso=true
    """
    estado     = ChoiceFilter(choices=EstadoEnvio.choices)
    ruta       = CharFilter(field_name='ruta__codigo', lookup_expr='iexact')
    remitente  = CharFilter(field_name='remitente__nro_doc')
    desde      = DateFilter(field_name='fecha_registro__date', lookup_expr='gte')
    hasta      = DateFilter(field_name='fecha_registro__date', lookup_expr='lte')
    con_retraso = CharFilter(method='filter_retraso', label='Con retraso (true/false)')

    def filter_retraso(self, queryset, name, value):
        """Filtra encomiendas con retraso usando el manager personalizado."""
        if value.lower() == 'true':
            return queryset.con_retraso()
        return queryset

    class Meta:
        model  = Encomienda
        fields = ['estado', 'ruta', 'remitente', 'desde', 'hasta', 'con_retraso']

# api/pagination.py
"""
Clases de paginación personalizadas para la API de encomiendas.
"""
from rest_framework.pagination import PageNumberPagination, LimitOffsetPagination, CursorPagination


class EncomiendaPagination(PageNumberPagination):
    """
    Paginación por número de página para encomiendas.
    Uso: GET /api/v1/encomiendas/?page=2&page_size=10
    """
    page_size = 15                    # default: 15 por página
    page_size_query_param = 'page_size'
    max_page_size = 100               # máximo permitido


class ClientePagination(PageNumberPagination):
    """
    Paginación para clientes: 20 por página.
    """
    page_size = 20
    page_size_query_param = 'page_size'
    max_page_size = 100


class HistorialPagination(LimitOffsetPagination):
    """
    Paginación por limit/offset para el historial de estados.
    Uso: GET /api/v1/encomiendas/1/historial/?limit=5&offset=10
    """
    default_limit = 10
    max_limit = 50


class EncomiendaCursorPagination(CursorPagination):
    """
    Paginación por cursor (más eficiente para grandes datasets).
    Ideal para feeds en tiempo real.
    """
    page_size = 15
    ordering = '-fecha_registro'

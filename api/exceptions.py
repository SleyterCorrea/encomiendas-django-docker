# api/exceptions.py
"""
Manejador de excepciones personalizado para la API de encomiendas.
Garantiza que TODOS los errores devuelvan el mismo formato JSON.
"""
from rest_framework.views import exception_handler
from rest_framework.response import Response
from rest_framework import status


def encomiendas_exception_handler(exc, context):
    """
    Manejador de excepciones personalizado.
    Devuelve siempre el mismo formato JSON:
    {
        "error": True,
        "status_code": 400,
        "message": "...",
        "details": {...}
    }
    """
    # Llamar al manejador por defecto de DRF primero
    response = exception_handler(exc, context)

    if response is not None:
        # Reestructurar la respuesta para un formato uniforme
        data = {
            'error': True,
            'status_code': response.status_code,
            'message': _get_message(response.status_code),
            'details': response.data,
        }
        response.data = data
    else:
        # Error no controlado (500)
        response = Response(
            {
                'error': True,
                'status_code': 500,
                'message': 'Error interno del servidor.',
                'details': str(exc),
            },
            status=status.HTTP_500_INTERNAL_SERVER_ERROR,
        )

    return response


def _get_message(status_code):
    messages = {
        400: 'Datos inválidos o solicitud incorrecta.',
        401: 'Autenticación requerida. Token inválido o expirado.',
        403: 'No tiene permisos para realizar esta acción.',
        404: 'El recurso solicitado no fue encontrado.',
        405: 'Método HTTP no permitido en este endpoint.',
        429: 'Demasiadas solicitudes. Intente más tarde.',
        500: 'Error interno del servidor.',
    }
    return messages.get(status_code, 'Ha ocurrido un error.')

# envios/async_services.py
"""
Sesi\u00f3n 07 \u2014 Servicios as\u00edncronos para broadcast al Channel Layer.

Estas funciones se llaman desde c\u00f3digo s\u00edncrono (ViewSets, Views)
y env\u00edan mensajes al Channel Layer de forma segura usando
async_to_sync de asgiref.

Funciones disponibles:
    notify_dashboard_update()         \u2014 Actualiza stats en todos los dashboards
    notify_encomienda_update(pk)      \u2014 Notifica cambio de estado en la encomienda pk
    notify_activity(mensaje)          \u2014 Publica en el feed global de actividad
    notify_bulk_progress(total, done) \u2014 Progreso de bulk_create en tiempo real
"""
import logging
from asgiref.sync import async_to_sync
from channels.layers import get_channel_layer
from django.utils import timezone

logger = logging.getLogger(__name__)


def _get_dashboard_stats():
    """Obtiene estad\u00edsticas del dashboard (s\u00edncrono)."""
    from envios.models import Encomienda
    from config.choices import EstadoEnvio
    hoy = timezone.now().date()
    return {
        'total_activas':  Encomienda.objects.activas().count(),
        'en_transito':    Encomienda.objects.en_transito().count(),
        'con_retraso':    Encomienda.objects.con_retraso().count(),
        'entregadas_hoy': Encomienda.objects.filter(
                              estado=EstadoEnvio.ENTREGADO,
                              fecha_entrega_real=hoy
                          ).count(),
        'timestamp':      timezone.now().isoformat(),
    }


def _get_encomienda_data(pk):
    """Obtiene datos de una encomienda para enviar al WebSocket."""
    from envios.models import Encomienda
    try:
        enc = Encomienda.objects.con_relaciones().get(pk=pk)
        return {
            'id':             enc.pk,
            'codigo':         enc.codigo,
            'estado':         enc.estado,
            'estado_display': enc.get_estado_display(),
            'timestamp':      timezone.now().isoformat(),
        }
    except Encomienda.DoesNotExist:
        return None


# \u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500
#  Funciones p\u00fablicas de notificaci\u00f3n
# \u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500

def notify_dashboard_update():
    """
    Env\u00eda las estad\u00edsticas actualizadas del dashboard
    a todos los clientes suscritos al grupo 'dashboard_stats'.

    Llamar despu\u00e9s de cualquier cambio de estado de encomienda.
    """
    try:
        channel_layer = get_channel_layer()
        if channel_layer is None:
            logger.warning('[WS] Channel layer no disponible')
            return

        stats = _get_dashboard_stats()
        async_to_sync(channel_layer.group_send)(
            'dashboard_stats',
            {
                'type':  'dashboard_update',  # nombre del m\u00e9todo en el consumer
                'stats': stats,
            }
        )
        logger.debug(f'[WS] Dashboard actualizado: {stats}')
    except Exception as exc:
        # No interrumpir el flujo normal si falla el WebSocket
        logger.error(f'[WS] Error al notificar dashboard: {exc}')


def notify_encomienda_update(pk):
    """
    Env\u00eda el nuevo estado de la encomienda `pk`
    a todos los clientes suscritos al grupo 'encomienda_{pk}'.

    Args:
        pk: ID de la encomienda actualizada
    """
    try:
        channel_layer = get_channel_layer()
        if channel_layer is None:
            return

        data = _get_encomienda_data(pk)
        if data is None:
            return

        async_to_sync(channel_layer.group_send)(
            f'encomienda_{pk}',
            {
                'type': 'estado_update',  # nombre del m\u00e9todo en EncomiendaConsumer
                'data': data,
            }
        )
        logger.debug(f'[WS] Encomienda {pk} actualizada')
    except Exception as exc:
        logger.error(f'[WS] Error al notificar encomienda {pk}: {exc}')


def notify_activity(mensaje, usuario=None):
    """
    Publica un mensaje en el feed global de actividad.
    Todos los empleados con el feed abierto lo ver\u00e1n al instante.

    Args:
        mensaje: Texto del evento a publicar
        usuario: Username del usuario que realiz\u00f3 la acci\u00f3n (opcional)
    """
    try:
        channel_layer = get_channel_layer()
        if channel_layer is None:
            return

        texto = f'[{usuario}] {mensaje}' if usuario else mensaje

        async_to_sync(channel_layer.group_send)(
            'activity_feed',
            {
                'type':      'activity',
                'mensaje':   texto,
                'timestamp': timezone.now().isoformat(),
            }
        )
        logger.debug(f'[WS] Activity feed: {texto}')
    except Exception as exc:
        logger.error(f'[WS] Error al publicar en activity feed: {exc}')


def notify_bulk_progress(total, done, encomienda_id=None, error=None):
    """
    Notifica el progreso de una operaci\u00f3n bulk_create en tiempo real.
    Publica en el feed de actividad el avance.

    Args:
        total:          Total de encomiendas a crear
        done:           Cu\u00e1ntas se han creado hasta ahora
        encomienda_id:  ID de la \u00faltima creada (opcional)
        error:          Mensaje de error si fall\u00f3 alguna (opcional)
    """
    try:
        channel_layer = get_channel_layer()
        if channel_layer is None:
            return

        porcentaje = round((done / total) * 100) if total > 0 else 0
        estado = 'error' if error else ('completado' if done == total else 'progreso')

        async_to_sync(channel_layer.group_send)(
            'activity_feed',
            {
                'type':    'activity',
                'mensaje': (
                    f'\U0001f4e6 Bulk create: {done}/{total} ({porcentaje}%) '
                    f'[\u2713 {encomienda_id}]' if encomienda_id else
                    f'\U0001f4e6 Bulk create: {done}/{total} ({porcentaje}%)'
                ),
                'timestamp': timezone.now().isoformat(),
                'extra': {
                    'tipo':       'bulk_progress',
                    'total':      total,
                    'done':       done,
                    'porcentaje': porcentaje,
                    'estado':     estado,
                    'error':      error,
                }
            }
        )
    except Exception as exc:
        logger.error(f'[WS] Error al notificar bulk progress: {exc}')

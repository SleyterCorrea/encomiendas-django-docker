# envios/consumers.py
"""
Sesi\u00f3n 07 \u2014 Consumers WebSocket del sistema de encomiendas.

Consumers implementados:
    DashboardConsumer     \u2014 grupo 'dashboard_stats'
        - Env\u00eda estad\u00edsticas actuales al conectar
        - Recibe broadcasts del sistema cuando cambian las stats
        - Permite refresh manual desde el cliente

    EncomiendaConsumer    \u2014 grupo 'encomienda_{pk}'
        - Sigue el estado de una encomienda espec\u00edfica
        - Notifica cambios de estado a los clientes suscritos

    ActivityFeedConsumer  \u2014 grupo 'activity_feed'
        - Feed global de actividad del sistema
        - Todos los empleados conectados ven los cambios
"""
import json
import logging
from channels.generic.websocket import AsyncWebsocketConsumer
from channels.db import database_sync_to_async
from django.utils import timezone

logger = logging.getLogger(__name__)


# \u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500
#  Helpers async para obtener datos de BD
# \u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500

@database_sync_to_async
def get_dashboard_stats():
    """Obtiene las estad\u00edsticas del dashboard desde la BD (versi\u00f3n async)."""
    from envios.models import Encomienda
    from config.choices import EstadoEnvio
    hoy = timezone.now().date()
    return {
        'total_activas':   Encomienda.objects.activas().count(),
        'en_transito':     Encomienda.objects.en_transito().count(),
        'con_retraso':     Encomienda.objects.con_retraso().count(),
        'entregadas_hoy':  Encomienda.objects.filter(
                               estado=EstadoEnvio.ENTREGADO,
                               fecha_entrega_real=hoy
                           ).count(),
        'timestamp':       timezone.now().isoformat(),
    }


@database_sync_to_async
def get_encomienda_data(pk):
    """Obtiene datos b\u00e1sicos de una encomienda por PK (versi\u00f3n async)."""
    from envios.models import Encomienda
    try:
        enc = Encomienda.objects.con_relaciones().get(pk=pk)
        return {
            'id':      enc.pk,
            'codigo':  enc.codigo,
            'estado':  enc.estado,
            'estado_display': enc.get_estado_display(),
            'timestamp': timezone.now().isoformat(),
        }
    except Encomienda.DoesNotExist:
        return None


# \u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500
#  Consumer 1: Dashboard en tiempo real
# \u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500

class DashboardConsumer(AsyncWebsocketConsumer):
    """
    WebSocket para el dashboard principal.

    Canal de grupo: 'dashboard_stats'
    Mensajes entrantes:
        {'action': 'refresh'}  \u2014 actualiza stats manualmente
    Mensajes salientes:
        {'type': 'dashboard_update', 'stats': {...}}
    """
    GROUP_NAME = 'dashboard_stats'

    async def connect(self):
        """Cliente se conecta: se une al grupo y recibe stats actuales."""
        # Rechazar conexiones no autenticadas
        if not self.scope['user'].is_authenticated:
            await self.close()
            return

        await self.channel_layer.group_add(self.GROUP_NAME, self.channel_name)
        await self.accept()
        logger.info(f'[WS] Dashboard conectado: usuario={self.scope["user"]}')

        # Env\u00eda estad\u00edsticas actuales al conectar
        stats = await get_dashboard_stats()
        await self.send(text_data=json.dumps({
            'type':  'dashboard_update',
            'stats': stats,
        }))

    async def disconnect(self, code):
        """Cliente se desconecta: sale del grupo."""
        await self.channel_layer.group_discard(self.GROUP_NAME, self.channel_name)
        logger.info(f'[WS] Dashboard desconectado: code={code}')

    async def receive(self, text_data):
        """Recibe mensajes del cliente (e.g., solicitud de refresh manual)."""
        try:
            data = json.loads(text_data)
        except json.JSONDecodeError:
            return

        if data.get('action') == 'refresh':
            stats = await get_dashboard_stats()
            await self.send(text_data=json.dumps({
                'type':  'dashboard_update',
                'stats': stats,
            }))

    # \u2500\u2500 Handler de grupo \u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500

    async def dashboard_update(self, event):
        """
        Handler llamado cuando el grupo recibe un broadcast.
        Re-env\u00eda el mensaje al cliente WebSocket conectado.
        """
        await self.send(text_data=json.dumps({
            'type':  'dashboard_update',
            'stats': event.get('stats', {}),
        }))


# \u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500
#  Consumer 2: Detalle de encomienda en tiempo real
# \u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500

class EncomiendaConsumer(AsyncWebsocketConsumer):
    """
    WebSocket para el detalle de una encomienda espec\u00edfica.

    Canal de grupo: 'encomienda_{pk}'
    Se notifica autom\u00e1ticamente cuando cambia el estado de esa encomienda.
    """

    @property
    def group_name(self):
        return f'encomienda_{self.pk}'

    async def connect(self):
        """Se une al grupo de esa encomienda espec\u00edfica."""
        self.pk = self.scope['url_route']['kwargs']['pk']

        if not self.scope['user'].is_authenticated:
            await self.close()
            return

        await self.channel_layer.group_add(self.group_name, self.channel_name)
        await self.accept()
        logger.info(f'[WS] Encomienda {self.pk} conectada')

        # Env\u00eda estado actual al conectar
        data = await get_encomienda_data(self.pk)
        if data:
            await self.send(text_data=json.dumps({
                'type': 'estado_update',
                'data': data,
            }))

    async def disconnect(self, code):
        """Sale del grupo al desconectar."""
        await self.channel_layer.group_discard(self.group_name, self.channel_name)
        logger.info(f'[WS] Encomienda {self.pk} desconectada: code={code}')

    async def receive(self, text_data):
        """Acepta mensajes del cliente (ack, sin acci\u00f3n por ahora)."""
        pass

    # \u2500\u2500 Handler de grupo \u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500

    async def estado_update(self, event):
        """
        Handler llamado cuando el grupo recibe un broadcast de cambio de estado.
        Re-env\u00eda el mensaje al cliente WebSocket.
        """
        await self.send(text_data=json.dumps({
            'type': 'estado_update',
            'data': event.get('data', {}),
        }))


# \u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500
#  Consumer 3: Feed global de actividad
# \u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500

class ActivityFeedConsumer(AsyncWebsocketConsumer):
    """
    WebSocket para el feed global de actividad del sistema.

    Canal de grupo: 'activity_feed'
    Todos los empleados conectados ven en tiempo real cada cambio de estado.
    """
    GROUP_NAME = 'activity_feed'

    async def connect(self):
        if not self.scope['user'].is_authenticated:
            await self.close()
            return

        await self.channel_layer.group_add(self.GROUP_NAME, self.channel_name)
        await self.accept()
        logger.info(f'[WS] ActivityFeed conectado: usuario={self.scope["user"]}')

        # Mensaje de bienvenida
        await self.send(text_data=json.dumps({
            'type':    'activity',
            'mensaje': f'\u2705 Conectado al feed de actividad como {self.scope["user"].username}',
            'timestamp': timezone.now().isoformat(),
        }))

    async def disconnect(self, code):
        await self.channel_layer.group_discard(self.GROUP_NAME, self.channel_name)

    async def receive(self, text_data):
        pass

    # \u2500\u2500 Handler de grupo \u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500

    async def activity(self, event):
        """Recibe un evento del grupo y lo manda al cliente."""
        await self.send(text_data=json.dumps({
            'type':    'activity',
            'mensaje': event.get('mensaje', ''),
            'timestamp': event.get('timestamp', timezone.now().isoformat()),
        }))

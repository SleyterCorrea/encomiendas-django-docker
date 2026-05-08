# envios/tests/test_api.py
"""
Tests automatizados para la API REST de encomiendas.

Cubre los 6 tests mínimos del entregable:
    1. list()           → GET /encomiendas/ devuelve 200
    2. create()         → POST /encomiendas/ crea con 201
    3. create() error   → POST con peso negativo devuelve 400
    4. retrieve()       → GET /encomiendas/{pk}/ devuelve detalle anidado
    5. cambiar_estado() → POST /encomiendas/{pk}/cambiar_estado/ cambia el estado
    6. 401 sin token    → Cualquier endpoint sin auth devuelve 401
    7. filtrar estado   → GET /encomiendas/?estado=PE filtra correctamente
    8. estadisticas()   → GET /encomiendas/estadisticas/ devuelve métricas
"""
from django.test import TestCase
from django.contrib.auth.models import User
from django.utils import timezone
from datetime import timedelta
from rest_framework.test import APIClient
from rest_framework import status

from envios.models import Encomienda, Empleado
from clientes.models import Cliente
from rutas.models import Ruta


class APIBaseTestCase(TestCase):
    """Clase base con setup compartido para todos los tests de la API."""

    def setUp(self):
        """Crear datos de prueba antes de cada test."""
        self.client = APIClient()

        # 1. Usuario admin
        self.user = User.objects.create_user(
            username='test_admin',
            email='test@encomiendas.com',
            password='TestPass123!',
            is_staff=True,
        )

        # 2. Empleado asociado al usuario
        self.empleado = Empleado.objects.create(
            codigo='EMP-TEST',
            nombres='Test',
            apellidos='Empleado',
            email='test@encomiendas.com',
            cargo='Administrador',
            fecha_ingreso=timezone.now().date(),
            estado=1,
        )

        # 3. Clientes de prueba
        self.remitente = Cliente.objects.create(
            tipo_doc='DNI', nro_doc='11111111',
            nombres='Juan', apellidos='Remitente', estado=1,
        )
        self.destinatario = Cliente.objects.create(
            tipo_doc='DNI', nro_doc='22222222',
            nombres='Maria', apellidos='Destinatario', estado=1,
        )

        # 4. Ruta de prueba
        self.ruta = Ruta.objects.create(
            codigo='TEST-RUT',
            origen='Lima', destino='Arequipa',
            precio_base=30.00, dias_entrega=3, estado=1,
        )

        # 5. Encomienda de prueba
        self.encomienda = Encomienda.objects.create(
            codigo='ENC-TEST-0001',
            descripcion='Encomienda de prueba',
            peso_kg=5.0,
            remitente=self.remitente,
            destinatario=self.destinatario,
            ruta=self.ruta,
            empleado_registro=self.empleado,
            estado='PE',
            costo_envio=35.00,
            fecha_entrega_est=timezone.now().date() + timedelta(days=5),
        )

        # 6. Obtener JWT token
        response = self.client.post('/api/v1/auth/token/', {
            'username': 'test_admin',
            'password': 'TestPass123!',
        }, format='json')
        self.token = response.data.get('access', '')
        self.client.credentials(HTTP_AUTHORIZATION=f'Bearer {self.token}')

    def get_url(self, path):
        return f'/api/v1/{path}'


class TestEncomiendaList(APIBaseTestCase):
    """Test 1: GET /encomiendas/ devuelve 200 y lista paginada."""

    def test_list_returns_200(self):
        response = self.client.get(self.get_url('encomiendas/'))
        self.assertEqual(response.status_code, status.HTTP_200_OK)

    def test_list_contains_count(self):
        response = self.client.get(self.get_url('encomiendas/'))
        self.assertIn('count', response.data)
        self.assertIn('results', response.data)

    def test_list_has_property_fields(self):
        """Verifica que los campos @property del modelo están en la respuesta."""
        response = self.client.get(self.get_url('encomiendas/'))
        if response.data['count'] > 0:
            enc = response.data['results'][0]
            self.assertIn('esta_entregada', enc)
            self.assertIn('tiene_retraso', enc)
            self.assertIn('dias_en_transito', enc)


class TestEncomiendaCreate(APIBaseTestCase):
    """Test 2: POST /encomiendas/ crea una encomienda con 201."""

    def test_create_returns_201(self):
        data = {
            'codigo': 'ENC-TEST-9999',
            'descripcion': 'Nueva encomienda de test',
            'peso_kg': 2.5,
            'remitente': self.remitente.id,
            'destinatario': self.destinatario.id,
            'ruta': self.ruta.id,
            'estado': 'PE',
            'costo_envio': 35.00,
            'fecha_entrega_est': str(timezone.now().date() + timedelta(days=4)),
        }
        response = self.client.post(self.get_url('encomiendas/'), data, format='json')
        self.assertEqual(response.status_code, status.HTTP_201_CREATED)
        self.assertEqual(response.data['codigo'], 'ENC-TEST-9999')


class TestEncomiendaCreateError(APIBaseTestCase):
    """Test 3: POST con datos inválidos devuelve 400."""

    def test_create_negative_weight_returns_400(self):
        """Peso negativo debe retornar 400."""
        data = {
            'codigo': 'ENC-BAD-001',
            'descripcion': 'Test peso negativo',
            'peso_kg': -1.0,   # ← inválido
            'remitente': self.remitente.id,
            'destinatario': self.destinatario.id,
            'ruta': self.ruta.id,
            'estado': 'PE',
            'costo_envio': 35.00,
            'fecha_entrega_est': str(timezone.now().date() + timedelta(days=4)),
        }
        response = self.client.post(self.get_url('encomiendas/'), data, format='json')
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)

    def test_create_same_remitente_destinatario_returns_400(self):
        """Remitente == destinatario debe retornar 400."""
        data = {
            'codigo': 'ENC-BAD-002',
            'descripcion': 'Test mismo cliente',
            'peso_kg': 3.0,
            'remitente': self.remitente.id,
            'destinatario': self.remitente.id,   # ← mismo cliente
            'ruta': self.ruta.id,
            'estado': 'PE',
            'costo_envio': 35.00,
            'fecha_entrega_est': str(timezone.now().date() + timedelta(days=4)),
        }
        response = self.client.post(self.get_url('encomiendas/'), data, format='json')
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)


class TestEncomiendaRetrieve(APIBaseTestCase):
    """Test 4: GET /encomiendas/{pk}/ devuelve detalle con objetos anidados."""

    def test_retrieve_returns_200(self):
        response = self.client.get(self.get_url(f'encomiendas/{self.encomienda.id}/'))
        self.assertEqual(response.status_code, status.HTTP_200_OK)

    def test_retrieve_has_nested_objects(self):
        """EncomiendaDetailSerializer debe devolver objetos anidados."""
        response = self.client.get(self.get_url(f'encomiendas/{self.encomienda.id}/'))
        data = response.data
        # remitente debe ser objeto, no int
        self.assertIsInstance(data.get('remitente'), dict)
        self.assertIsInstance(data.get('ruta'), dict)
        self.assertIn('historial', data)


class TestEncomiendaCambiarEstado(APIBaseTestCase):
    """Test 5: POST /encomiendas/{pk}/cambiar_estado/ cambia el estado."""

    def test_cambiar_estado_to_transito(self):
        response = self.client.post(
            self.get_url(f'encomiendas/{self.encomienda.id}/cambiar_estado/'),
            {'estado': 'TR', 'observacion': 'En camino'},
            format='json',
        )
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.encomienda.refresh_from_db()
        self.assertEqual(self.encomienda.estado, 'TR')

    def test_cambiar_estado_invalido_returns_400(self):
        response = self.client.post(
            self.get_url(f'encomiendas/{self.encomienda.id}/cambiar_estado/'),
            {'estado': 'XX'},   # ← estado inválido
            format='json',
        )
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)


class TestEncomiendaSinToken(APIBaseTestCase):
    """Test 6: Sin token → 401 Unauthorized."""

    def test_list_sin_token_returns_401(self):
        self.client.credentials()  # elimina las credenciales
        response = self.client.get(self.get_url('encomiendas/'))
        self.assertEqual(response.status_code, status.HTTP_401_UNAUTHORIZED)

    def test_error_format_uniforme(self):
        """El exception handler devuelve formato uniforme."""
        self.client.credentials()
        response = self.client.get(self.get_url('encomiendas/'))
        # Formato: {'error': True, 'status_code': 401, 'message': '...'}
        self.assertIn('error', response.data)
        self.assertTrue(response.data['error'])


class TestEncomiendaFiltros(APIBaseTestCase):
    """Test 7: Filtros por estado, búsqueda y ordenamiento."""

    def test_filtrar_por_estado(self):
        response = self.client.get(self.get_url('encomiendas/?estado=PE'))
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        for enc in response.data.get('results', []):
            self.assertEqual(enc['estado'], 'PE')

    def test_search_funciona(self):
        response = self.client.get(self.get_url('encomiendas/?search=TEST'))
        self.assertEqual(response.status_code, status.HTTP_200_OK)


class TestEncomiendaEstadisticas(APIBaseTestCase):
    """Test 8: GET /encomiendas/estadisticas/ devuelve métricas."""

    def test_estadisticas_returns_200(self):
        response = self.client.get(self.get_url('encomiendas/estadisticas/'))
        self.assertEqual(response.status_code, status.HTTP_200_OK)

    def test_estadisticas_tiene_campos(self):
        response = self.client.get(self.get_url('encomiendas/estadisticas/'))
        data = response.data
        self.assertIn('total', data)
        self.assertIn('pendientes', data)
        self.assertIn('entregadas', data)
        self.assertIn('con_retraso', data)

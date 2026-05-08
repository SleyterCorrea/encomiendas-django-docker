# envios/management/commands/seed_data.py
"""
Comando para poblar la base de datos con datos de prueba.
Uso: docker compose exec web python manage.py seed_data
"""
from django.core.management.base import BaseCommand
from django.contrib.auth.models import User
from django.utils import timezone
from datetime import date, timedelta
import random

from clientes.models import Cliente
from rutas.models import Ruta
from envios.models import Empleado, Encomienda, HistorialEstado
from config.choices import EstadoGeneral, EstadoEnvio, TipoDocumento


class Command(BaseCommand):
    help = 'Pobla la base de datos con datos de prueba (clientes, rutas, empleados, encomiendas)'

    def add_arguments(self, parser):
        parser.add_argument(
            '--clear',
            action='store_true',
            help='Eliminar datos existentes antes de insertar',
        )

    def handle(self, *args, **options):
        if options['clear']:
            self.stdout.write(self.style.WARNING('⚠️  Eliminando datos existentes...'))
            HistorialEstado.objects.all().delete()
            Encomienda.objects.all().delete()
            Empleado.objects.all().delete()
            Ruta.objects.all().delete()
            Cliente.objects.all().delete()
            self.stdout.write(self.style.SUCCESS('✅ Datos eliminados.'))

        self.stdout.write(self.style.MIGRATE_HEADING('\n🌱 Iniciando seed de datos...\n'))

        # ─────────────────────────────────────────
        # 1. CLIENTES
        # ─────────────────────────────────────────
        clientes_data = [
            {
                'tipo_doc': TipoDocumento.DNI,
                'nro_doc': '45123678',
                'nombres': 'Carlos Alberto',
                'apellidos': 'Ramírez Torres',
                'telefono': '987654321',
                'email': 'carlos.ramirez@gmail.com',
                'direccion': 'Av. Arequipa 1234, Lima',
            },
            {
                'tipo_doc': TipoDocumento.DNI,
                'nro_doc': '72345891',
                'nombres': 'María Elena',
                'apellidos': 'Gutiérrez Flores',
                'telefono': '976543210',
                'email': 'maria.gutierrez@hotmail.com',
                'direccion': 'Jr. Huancayo 567, Lima',
            },
            {
                'tipo_doc': TipoDocumento.DNI,
                'nro_doc': '61234789',
                'nombres': 'José Luis',
                'apellidos': 'Mendoza Quispe',
                'telefono': '965432109',
                'email': 'jmendoza@yahoo.com',
                'direccion': 'Calle Los Álamos 890, Arequipa',
            },
            {
                'tipo_doc': TipoDocumento.RUC,
                'nro_doc': '20512345678',
                'nombres': 'Distribuciones',
                'apellidos': 'Norte SAC',
                'telefono': '01-4567890',
                'email': 'ventas@distnorte.com',
                'direccion': 'Av. Industrial 2345, Trujillo',
            },
            {
                'tipo_doc': TipoDocumento.DNI,
                'nro_doc': '48765432',
                'nombres': 'Ana Sofía',
                'apellidos': 'Paredes Villanueva',
                'telefono': '954321098',
                'email': 'ana.paredes@gmail.com',
                'direccion': 'Psje. Los Jazmines 12, Cusco',
            },
            {
                'tipo_doc': TipoDocumento.DNI,
                'nro_doc': '53219876',
                'nombres': 'Roberto',
                'apellidos': 'Castillo Medina',
                'telefono': '943210987',
                'email': 'rcastillo@outlook.com',
                'direccion': 'Jr. Loreto 456, Iquitos',
            },
            {
                'tipo_doc': TipoDocumento.PASAPORTE,
                'nro_doc': 'AB123456',
                'nombres': 'Giovanni',
                'apellidos': 'Rossi',
                'telefono': '932109876',
                'email': 'g.rossi@gmail.com',
                'direccion': 'Av. La Marina 789, Lima',
            },
            {
                'tipo_doc': TipoDocumento.DNI,
                'nro_doc': '41098765',
                'nombres': 'Lucía Carmen',
                'apellidos': 'Huanca Mamani',
                'telefono': '921098765',
                'email': 'lucia.huanca@gmail.com',
                'direccion': 'Av. El Sol 321, Puno',
            },
        ]

        clientes = []
        for data in clientes_data:
            obj, created = Cliente.objects.get_or_create(
                nro_doc=data['nro_doc'],
                defaults=data,
            )
            clientes.append(obj)
            if created:
                self.stdout.write(f'  ✅ Cliente: {obj}')
            else:
                self.stdout.write(f'  ⏭️  Ya existe: {obj}')

        self.stdout.write(self.style.SUCCESS(f'\n✔ {len(clientes)} clientes listos.\n'))

        # ─────────────────────────────────────────
        # 2. RUTAS
        # ─────────────────────────────────────────
        rutas_data = [
            {
                'codigo': 'LIM-AQP',
                'origen': 'Lima',
                'destino': 'Arequipa',
                'descripcion': 'Ruta Lima - Arequipa via Panamericana Sur',
                'precio_base': 35.00,
                'dias_entrega': 2,
            },
            {
                'codigo': 'LIM-TRU',
                'origen': 'Lima',
                'destino': 'Trujillo',
                'descripcion': 'Ruta Lima - Trujillo via Panamericana Norte',
                'precio_base': 25.00,
                'dias_entrega': 1,
            },
            {
                'codigo': 'LIM-CUS',
                'origen': 'Lima',
                'destino': 'Cusco',
                'descripcion': 'Ruta Lima - Cusco via Los Libertadores',
                'precio_base': 50.00,
                'dias_entrega': 3,
            },
            {
                'codigo': 'LIM-IQU',
                'origen': 'Lima',
                'destino': 'Iquitos',
                'descripcion': 'Ruta Lima - Iquitos (carga aérea)',
                'precio_base': 80.00,
                'dias_entrega': 2,
            },
            {
                'codigo': 'AQP-CUS',
                'origen': 'Arequipa',
                'destino': 'Cusco',
                'descripcion': 'Ruta Arequipa - Cusco via altiplano',
                'precio_base': 30.00,
                'dias_entrega': 2,
            },
            {
                'codigo': 'TRU-PIU',
                'origen': 'Trujillo',
                'destino': 'Piura',
                'descripcion': 'Ruta Trujillo - Piura via Panamericana Norte',
                'precio_base': 20.00,
                'dias_entrega': 1,
            },
            {
                'codigo': 'LIM-HYO',
                'origen': 'Lima',
                'destino': 'Huancayo',
                'descripcion': 'Ruta Lima - Huancayo via Carretera Central',
                'precio_base': 22.00,
                'dias_entrega': 1,
            },
            {
                'codigo': 'LIM-PUN',
                'origen': 'Lima',
                'destino': 'Puno',
                'descripcion': 'Ruta Lima - Puno via Sur Peruano',
                'precio_base': 60.00,
                'dias_entrega': 4,
            },
        ]

        rutas = []
        for data in rutas_data:
            obj, created = Ruta.objects.get_or_create(
                codigo=data['codigo'],
                defaults=data,
            )
            rutas.append(obj)
            if created:
                self.stdout.write(f'  ✅ Ruta: {obj}')
            else:
                self.stdout.write(f'  ⏭️  Ya existe: {obj}')

        self.stdout.write(self.style.SUCCESS(f'\n✔ {len(rutas)} rutas listas.\n'))

        # ─────────────────────────────────────────
        # 3. EMPLEADOS
        # ─────────────────────────────────────────
        hoy = date.today()
        empleados_data = [
            {
                'codigo': 'EMP-001',
                'nombres': 'Pedro',
                'apellidos': 'Sánchez López',
                'cargo': 'Jefe de Operaciones',
                'email': 'pedro.sanchez@encomiendas.com',
                'telefono': '999000001',
                'fecha_ingreso': hoy - timedelta(days=365 * 3),
            },
            {
                'codigo': 'EMP-002',
                'nombres': 'Sofía',
                'apellidos': 'Vargas Ríos',
                'cargo': 'Operadora de Envíos',
                'email': 'sofia.vargas@encomiendas.com',
                'telefono': '999000002',
                'fecha_ingreso': hoy - timedelta(days=365 * 2),
            },
            {
                'codigo': 'EMP-003',
                'nombres': 'Miguel',
                'apellidos': 'Torres Cáceres',
                'cargo': 'Repartidor',
                'email': 'miguel.torres@encomiendas.com',
                'telefono': '999000003',
                'fecha_ingreso': hoy - timedelta(days=180),
            },
        ]

        empleados = []
        for data in empleados_data:
            obj, created = Empleado.objects.get_or_create(
                codigo=data['codigo'],
                defaults=data,
            )
            if created:
                # Asignar rutas aleatorias al empleado
                rutas_asignadas = random.sample(rutas, k=min(3, len(rutas)))
                obj.rutas_asignadas.set(rutas_asignadas)
                self.stdout.write(f'  ✅ Empleado: {obj}')
            else:
                self.stdout.write(f'  ⏭️  Ya existe: {obj}')
            empleados.append(obj)

        self.stdout.write(self.style.SUCCESS(f'\n✔ {len(empleados)} empleados listos.\n'))

        # ─────────────────────────────────────────
        # 4. ENCOMIENDAS
        # ─────────────────────────────────────────
        self.stdout.write('Creando encomiendas...')

        encomiendas_data = [
            {
                'descripcion': 'Laptop HP Pavilion 15 pulgadas en caja original',
                'peso_kg': 3.5,
                'remitente_idx': 0,
                'destinatario_idx': 2,
                'ruta_idx': 0,
                'empleado_idx': 0,
                'estado': EstadoEnvio.ENTREGADO,
                'dias_atras': 10,
            },
            {
                'descripcion': 'Ropa y calzado deportivo (2 bolsas)',
                'peso_kg': 6.0,
                'remitente_idx': 1,
                'destinatario_idx': 3,
                'ruta_idx': 1,
                'empleado_idx': 1,
                'estado': EstadoEnvio.EN_TRANSITO,
                'dias_atras': 2,
            },
            {
                'descripcion': 'Documentos legales urgentes notariados',
                'peso_kg': 0.5,
                'remitente_idx': 2,
                'destinatario_idx': 4,
                'ruta_idx': 6,
                'empleado_idx': 1,
                'estado': EstadoEnvio.PENDIENTE,
                'dias_atras': 0,
            },
            {
                'descripcion': 'Repuestos electrónicos para computadora (3 cajas)',
                'peso_kg': 8.2,
                'remitente_idx': 3,
                'destinatario_idx': 0,
                'ruta_idx': 2,
                'empleado_idx': 0,
                'estado': EstadoEnvio.EN_DESTINO,
                'dias_atras': 4,
            },
            {
                'descripcion': 'Artesanías de madera tallada empacadas',
                'peso_kg': 12.0,
                'remitente_idx': 4,
                'destinatario_idx': 1,
                'ruta_idx': 4,
                'empleado_idx': 2,
                'estado': EstadoEnvio.ENTREGADO,
                'dias_atras': 7,
            },
            {
                'descripcion': 'Medicamentos refrigerados con cadena de frío',
                'peso_kg': 2.3,
                'remitente_idx': 5,
                'destinatario_idx': 6,
                'ruta_idx': 3,
                'empleado_idx': 1,
                'estado': EstadoEnvio.PENDIENTE,
                'dias_atras': 1,
            },
            {
                'descripcion': 'Cámara fotográfica profesional con accesorios',
                'peso_kg': 4.7,
                'remitente_idx': 6,
                'destinatario_idx': 7,
                'ruta_idx': 5,
                'empleado_idx': 0,
                'estado': EstadoEnvio.EN_TRANSITO,
                'dias_atras': 3,
            },
            {
                'descripcion': 'Libros universitarios (caja grande)',
                'peso_kg': 15.0,
                'remitente_idx': 7,
                'destinatario_idx': 5,
                'ruta_idx': 7,
                'empleado_idx': 2,
                'estado': EstadoEnvio.PENDIENTE,
                'dias_atras': 0,
            },
        ]

        encomiendas_creadas = 0
        for i, data in enumerate(encomiendas_data):
            remitente = clientes[data['remitente_idx']]
            destinatario = clientes[data['destinatario_idx']]
            ruta = rutas[data['ruta_idx']]
            empleado = empleados[data['empleado_idx']]

            # Calcular fecha_entrega_est en el futuro o pasado según estado
            dias_atras = data['dias_atras']
            fecha_registro = timezone.now() - timedelta(days=dias_atras)
            fecha_entrega_est = fecha_registro.date() + timedelta(days=ruta.dias_entrega)

            # Para entregados, si la fecha ya pasó la usamos tal cual
            fecha_entrega_real = None
            if data['estado'] == EstadoEnvio.ENTREGADO:
                fecha_entrega_real = fecha_entrega_est

            # Código único
            from django.utils import timezone as tz
            import uuid
            codigo = (
                f"ENC-{fecha_registro.strftime('%Y%m%d')}"
                f"-{str(uuid.uuid4())[:6].upper()}"
            )

            # Calcular costo
            PRECIO_POR_KG_EXTRA = 2.50
            PESO_BASE = 5.0
            costo = float(ruta.precio_base)
            peso = data['peso_kg']
            if peso > PESO_BASE:
                costo += (peso - PESO_BASE) * PRECIO_POR_KG_EXTRA

            try:
                enc = Encomienda(
                    codigo=codigo,
                    descripcion=data['descripcion'],
                    peso_kg=peso,
                    remitente=remitente,
                    destinatario=destinatario,
                    ruta=ruta,
                    empleado_registro=empleado,
                    estado=data['estado'],
                    costo_envio=round(costo, 2),
                    fecha_entrega_est=fecha_entrega_est,
                    fecha_entrega_real=fecha_entrega_real,
                )
                # Bypass full_clean para fechas pasadas en datos semilla
                Encomienda.objects.bulk_create([enc])
                encomiendas_creadas += 1
                self.stdout.write(f'  ✅ Encomienda {codigo}: {remitente.nombres} → {destinatario.nombres}')
            except Exception as e:
                self.stdout.write(self.style.WARNING(f'  ⚠️  Encomienda {i+1} omitida: {e}'))

        self.stdout.write(self.style.SUCCESS(f'\n✔ {encomiendas_creadas} encomiendas creadas.\n'))

        # ─────────────────────────────────────────
        # RESUMEN FINAL
        # ─────────────────────────────────────────
        self.stdout.write(self.style.MIGRATE_HEADING('=' * 50))
        self.stdout.write(self.style.SUCCESS('🎉 Seed completado exitosamente!'))
        self.stdout.write(self.style.MIGRATE_HEADING('=' * 50))
        self.stdout.write(f'  Clientes  : {Cliente.objects.count()}')
        self.stdout.write(f'  Rutas     : {Ruta.objects.count()}')
        self.stdout.write(f'  Empleados : {Empleado.objects.count()}')
        self.stdout.write(f'  Encomiendas: {Encomienda.objects.count()}')
        self.stdout.write('')
        self.stdout.write('  👉 Accede al admin en: http://localhost:8001/admin')
        self.stdout.write(self.style.MIGRATE_HEADING('=' * 50))

# envios/serializers.py
"""
Serializers del sistema de encomiendas.

Jerarquía:
    ClienteSerializer       → para embed en EncomiendaDetailSerializer
    RutaSerializer          → para embed en EncomiendaDetailSerializer
    HistorialEstadoSerializer → para historial anidado
    EncomiendaSerializer    → creación/listado (IDs en relaciones)
    EncomiendaDetailSerializer → detalle (objetos anidados completos)
"""
from rest_framework import serializers
from django.utils import timezone

from .models import Encomienda, HistorialEstado, Empleado
from clientes.models import Cliente
from rutas.models import Ruta


# ─────────────────────────────────────────────────────────────────────────────
#  Serializers de apoyo (usados como nested en EncomiendaDetailSerializer)
# ─────────────────────────────────────────────────────────────────────────────

class ClienteSerializer(serializers.ModelSerializer):
    """Serializer de clientes. Expone @property del modelo."""
    # @property del modelo expuestas como campos de solo lectura
    nombre_completo = serializers.ReadOnlyField()
    esta_activo     = serializers.ReadOnlyField()

    class Meta:
        model  = Cliente
        fields = [
            'id', 'tipo_doc', 'nro_doc',
            'nombres', 'apellidos', 'nombre_completo',
            'telefono', 'email', 'esta_activo',
        ]


class RutaSerializer(serializers.ModelSerializer):
    """Serializer de rutas."""
    class Meta:
        model  = Ruta
        fields = [
            'id', 'codigo', 'origen', 'destino',
            'precio_base', 'dias_entrega', 'estado',
        ]


class HistorialEstadoSerializer(serializers.ModelSerializer):
    """
    Serializer del historial de cambios de estado.
    Expone displays legibles de los estados.
    """
    empleado_nombre      = serializers.ReadOnlyField(source='empleado.__str__')
    estado_anterior_display = serializers.CharField(
        source='get_estado_anterior_display', read_only=True
    )
    estado_nuevo_display = serializers.CharField(
        source='get_estado_nuevo_display', read_only=True
    )

    class Meta:
        model  = HistorialEstado
        fields = [
            'id', 'estado_anterior', 'estado_anterior_display',
            'estado_nuevo', 'estado_nuevo_display',
            'empleado_nombre', 'observacion', 'fecha_cambio',
        ]


# ─────────────────────────────────────────────────────────────────────────────
#  EncomiendaSerializer — para listado y creación
# ─────────────────────────────────────────────────────────────────────────────

class EncomiendaSerializer(serializers.ModelSerializer):
    """
    Serializer principal de encomiendas.
    - Listado: muestra IDs de relaciones + propiedades calculadas
    - Creación/Edición: acepta IDs para las relaciones FK
    """
    # Propiedades @property del modelo como campos de solo lectura
    esta_entregada   = serializers.ReadOnlyField()
    tiene_retraso    = serializers.ReadOnlyField()
    dias_en_transito = serializers.ReadOnlyField()
    descripcion_corta = serializers.ReadOnlyField()

    # Campo calculado con método
    estado_display = serializers.SerializerMethodField()

    class Meta:
        model  = Encomienda
        fields = [
            'id', 'codigo', 'descripcion', 'descripcion_corta',
            'peso_kg', 'volumen_cm3',
            'remitente', 'destinatario', 'ruta', 'empleado_registro',
            'estado', 'estado_display',
            'costo_envio',
            'fecha_registro', 'fecha_entrega_est', 'fecha_entrega_real',
            'observaciones',
            # Propiedades calculadas
            'esta_entregada', 'tiene_retraso', 'dias_en_transito',
        ]
        read_only_fields = ['id', 'fecha_registro', 'empleado_registro']

    def get_estado_display(self, obj):
        """Devuelve el label legible del estado."""
        return obj.get_estado_display()

    # ── Validaciones de campo ─────────────────────────────────────

    def validate_peso_kg(self, value):
        """El peso debe estar entre 0.01 y 500 kg."""
        if value <= 0:
            raise serializers.ValidationError('El peso debe ser mayor a 0 kg.')
        if value > 500:
            raise serializers.ValidationError('El peso máximo permitido es 500 kg.')
        return value

    def validate_codigo(self, value):
        """El código debe comenzar con ENC-."""
        if not value.startswith('ENC-'):
            raise serializers.ValidationError("El código debe comenzar con 'ENC-'.")
        return value.upper()

    def validate_costo_envio(self, value):
        """El costo no puede ser negativo."""
        if value < 0:
            raise serializers.ValidationError('El costo no puede ser negativo.')
        return value

    # ── Validación cruzada ────────────────────────────────────────

    def validate(self, data):
        """Reglas que involucran más de un campo."""
        errors = {}

        # Regla 1: remitente != destinatario
        remitente    = data.get('remitente',    getattr(self.instance, 'remitente', None))
        destinatario = data.get('destinatario', getattr(self.instance, 'destinatario', None))
        if remitente and destinatario and remitente == destinatario:
            errors['destinatario'] = 'El destinatario no puede ser el mismo que el remitente.'

        # Regla 2: fecha estimada no en el pasado
        fecha_est = data.get('fecha_entrega_est')
        if fecha_est and fecha_est < timezone.now().date():
            errors['fecha_entrega_est'] = 'La fecha estimada no puede ser en el pasado.'

        # Regla 3: costo mínimo según la ruta
        ruta  = data.get('ruta',  getattr(self.instance, 'ruta', None))
        costo = data.get('costo_envio')
        if ruta and costo is not None and costo < float(ruta.precio_base):
            errors['costo_envio'] = f'El costo mínimo para esta ruta es S/ {ruta.precio_base}.'

        if errors:
            raise serializers.ValidationError(errors)
        return data

    # ── to_representation: oculta campos según el usuario ─────────

    def to_representation(self, instance):
        """
        Personaliza la salida JSON según el usuario:
        - Usuarios no-staff: NO ven 'empleado_registro' ni 'observaciones'
        - Usuarios staff/admin: ven todos los campos
        """
        data    = super().to_representation(instance)
        request = self.context.get('request')

        if request and not request.user.is_staff:
            # Empleados regulares no ven datos internos
            data.pop('empleado_registro', None)
            data.pop('observaciones', None)

        return data


# ─────────────────────────────────────────────────────────────────────────────
#  EncomiendaDetailSerializer — para detalle con objetos anidados
# ─────────────────────────────────────────────────────────────────────────────

class EncomiendaDetailSerializer(serializers.ModelSerializer):
    """
    Serializer de detalle de encomiendas.
    - GET:  devuelve objetos anidados completos (remitente, destinatario, ruta)
    - POST/PUT/PATCH: acepta solo IDs (write_only fields)
    """
    # ── Campos de solo lectura: objetos anidados completos ────────
    remitente    = ClienteSerializer(read_only=True)
    destinatario = ClienteSerializer(read_only=True)
    ruta         = RutaSerializer(read_only=True)

    # ── Campos de solo escritura: aceptar ID para crear/actualizar
    remitente_id = serializers.PrimaryKeyRelatedField(
        queryset=Cliente.objects.activos(),
        write_only=True, source='remitente'
    )
    destinatario_id = serializers.PrimaryKeyRelatedField(
        queryset=Cliente.objects.activos(),
        write_only=True, source='destinatario'
    )
    ruta_id = serializers.PrimaryKeyRelatedField(
        queryset=Ruta.objects.activas(),
        write_only=True, source='ruta'
    )

    # ── Historial: los últimos 5 cambios de estado ─────────────────
    historial = serializers.SerializerMethodField()

    # ── Propiedades del modelo ────────────────────────────────────
    esta_entregada   = serializers.ReadOnlyField()
    tiene_retraso    = serializers.ReadOnlyField()
    dias_en_transito = serializers.ReadOnlyField()
    descripcion_corta = serializers.ReadOnlyField()
    estado_display   = serializers.SerializerMethodField()

    class Meta:
        model  = Encomienda
        fields = [
            'id', 'codigo', 'descripcion', 'descripcion_corta',
            'peso_kg', 'volumen_cm3',
            # Relaciones (lectura = objetos, escritura = IDs)
            'remitente', 'remitente_id',
            'destinatario', 'destinatario_id',
            'ruta', 'ruta_id',
            'empleado_registro',
            # Estado
            'estado', 'estado_display',
            'costo_envio',
            # Fechas
            'fecha_registro', 'fecha_entrega_est', 'fecha_entrega_real',
            'observaciones',
            # Propiedades calculadas
            'esta_entregada', 'tiene_retraso', 'dias_en_transito',
            # Historial anidado
            'historial',
        ]
        read_only_fields = ['id', 'fecha_registro', 'empleado_registro']

    def get_estado_display(self, obj):
        return obj.get_estado_display()

    def get_historial(self, obj):
        """Devuelve los últimos 5 cambios de estado."""
        qs = obj.historial.all()[:5]
        return HistorialEstadoSerializer(qs, many=True).data

    def validate_peso_kg(self, value):
        if value <= 0:
            raise serializers.ValidationError('El peso debe ser mayor a 0 kg.')
        if value > 500:
            raise serializers.ValidationError('El peso máximo permitido es 500 kg.')
        return value

    def validate_codigo(self, value):
        if not value.startswith('ENC-'):
            raise serializers.ValidationError("El código debe comenzar con 'ENC-'.")
        return value.upper()

    def validate(self, data):
        errors = {}
        remitente    = data.get('remitente',    getattr(self.instance, 'remitente', None))
        destinatario = data.get('destinatario', getattr(self.instance, 'destinatario', None))
        if remitente and destinatario and remitente == destinatario:
            errors['destinatario'] = 'El destinatario no puede ser el mismo que el remitente.'
        fecha_est = data.get('fecha_entrega_est')
        if fecha_est and fecha_est < timezone.now().date():
            errors['fecha_entrega_est'] = 'La fecha estimada no puede ser en el pasado.'
        if errors:
            raise serializers.ValidationError(errors)
        return data


# ─────────────────────────────────────────────────────────────────────────────
#  EncomiendaV2Serializer — API v2 (campos simplificados)
# ─────────────────────────────────────────────────────────────────────────────

class EncomiendaV2Serializer(serializers.ModelSerializer):
    """
    Serializer para API v2 — respuesta simplificada y más limpia.

    Diferencias respecto a v1:
    - Incluye 'url' del recurso (HyperlinkedField)
    - Solo campos esenciales (menos verboso)
    - Nombres de campos en snake_case más cortos
    - Agrega campo 'resumen' con estado y retraso juntos
    """
    url          = serializers.HyperlinkedIdentityField(
        view_name='encomienda-detail', read_only=True
    )
    estado_label = serializers.CharField(source='get_estado_display', read_only=True)
    con_retraso  = serializers.ReadOnlyField(source='tiene_retraso')
    resumen      = serializers.SerializerMethodField()

    class Meta:
        model  = Encomienda
        fields = [
            'url', 'id', 'codigo',
            'peso_kg', 'costo_envio',
            'remitente', 'destinatario', 'ruta',
            'estado', 'estado_label', 'con_retraso',
            'fecha_registro', 'fecha_entrega_est',
            'resumen',
        ]

    def get_resumen(self, obj):
        """Campo nuevo en v2: resumen en texto del estado actual."""
        retraso = ' ⚠ CON RETRASO' if obj.tiene_retraso else ''
        return f'{obj.get_estado_display()}{retraso}'


class EncomiendaDetailSerializer(serializers.ModelSerializer):
    """
    Serializer de detalle de encomiendas.
    - GET:  devuelve objetos anidados completos (remitente, destinatario, ruta)
    - POST/PUT/PATCH: acepta solo IDs (write_only fields)
    """
    # ── Campos de solo lectura: objetos anidados completos ────────
    remitente    = ClienteSerializer(read_only=True)
    destinatario = ClienteSerializer(read_only=True)
    ruta         = RutaSerializer(read_only=True)

    # ── Campos de solo escritura: aceptar ID para crear/actualizar
    remitente_id = serializers.PrimaryKeyRelatedField(
        queryset=Cliente.objects.activos(),
        write_only=True, source='remitente'
    )
    destinatario_id = serializers.PrimaryKeyRelatedField(
        queryset=Cliente.objects.activos(),
        write_only=True, source='destinatario'
    )
    ruta_id = serializers.PrimaryKeyRelatedField(
        queryset=Ruta.objects.activas(),
        write_only=True, source='ruta'
    )

    # ── Historial: los últimos 5 cambios de estado ─────────────────
    historial = serializers.SerializerMethodField()

    # ── Propiedades del modelo ────────────────────────────────────
    esta_entregada   = serializers.ReadOnlyField()
    tiene_retraso    = serializers.ReadOnlyField()
    dias_en_transito = serializers.ReadOnlyField()
    descripcion_corta = serializers.ReadOnlyField()
    estado_display   = serializers.SerializerMethodField()

    class Meta:
        model  = Encomienda
        fields = [
            'id', 'codigo', 'descripcion', 'descripcion_corta',
            'peso_kg', 'volumen_cm3',
            # Relaciones (lectura = objetos, escritura = IDs)
            'remitente', 'remitente_id',
            'destinatario', 'destinatario_id',
            'ruta', 'ruta_id',
            'empleado_registro',
            # Estado
            'estado', 'estado_display',
            'costo_envio',
            # Fechas
            'fecha_registro', 'fecha_entrega_est', 'fecha_entrega_real',
            'observaciones',
            # Propiedades calculadas
            'esta_entregada', 'tiene_retraso', 'dias_en_transito',
            # Historial anidado
            'historial',
        ]
        read_only_fields = ['id', 'fecha_registro', 'empleado_registro']

    def get_estado_display(self, obj):
        return obj.get_estado_display()

    def get_historial(self, obj):
        """Devuelve los últimos 5 cambios de estado."""
        qs = obj.historial.all()[:5]
        return HistorialEstadoSerializer(qs, many=True).data

    def validate_peso_kg(self, value):
        if value <= 0:
            raise serializers.ValidationError('El peso debe ser mayor a 0 kg.')
        if value > 500:
            raise serializers.ValidationError('El peso máximo permitido es 500 kg.')
        return value

    def validate_codigo(self, value):
        if not value.startswith('ENC-'):
            raise serializers.ValidationError("El código debe comenzar con 'ENC-'.")
        return value.upper()

    def validate(self, data):
        errors = {}
        remitente    = data.get('remitente',    getattr(self.instance, 'remitente', None))
        destinatario = data.get('destinatario', getattr(self.instance, 'destinatario', None))
        if remitente and destinatario and remitente == destinatario:
            errors['destinatario'] = 'El destinatario no puede ser el mismo que el remitente.'
        fecha_est = data.get('fecha_entrega_est')
        if fecha_est and fecha_est < timezone.now().date():
            errors['fecha_entrega_est'] = 'La fecha estimada no puede ser en el pasado.'
        if errors:
            raise serializers.ValidationError(errors)
        return data

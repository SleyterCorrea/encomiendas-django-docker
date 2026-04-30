# envios/admin.py
from django.contrib import admin
from django.utils.html import format_html
from .models import Empleado, Encomienda, HistorialEstado

# ── Personalización del título del Admin ──────────────────────────────────────
admin.site.site_header  = '📦 Sistema de Encomiendas'
admin.site.site_title   = 'Encomiendas Admin'
admin.site.index_title  = 'Panel de Administración'


# ── Mapa de colores por estado ────────────────────────────────────────────────
ESTADO_COLORS = {
    'PE': ('#856404', '#fff3cd'),   # Pendiente   → amarillo
    'TR': ('#0c5460', '#d1ecf1'),   # En tránsito → azul celeste
    'DE': ('#155724', '#d4edda'),   # En destino  → verde suave
    'EN': ('#155724', '#28a745'),   # Entregado   → verde
    'DV': ('#721c24', '#f8d7da'),   # Devuelto    → rojo
}


@admin.register(Encomienda)
class EncomiendaAdmin(admin.ModelAdmin):

    # ── Columnas en la lista ───────────────────────────────────────────────────
    list_display   = (
        'codigo', 'remitente', 'destinatario', 'ruta',
        'estado_badge', 'costo_envio', 'fecha_registro',
    )
    list_filter    = ('estado', 'ruta')
    search_fields  = ('codigo', 'remitente__nro_doc', 'destinatario__nro_doc',
                      'remitente__apellidos', 'destinatario__apellidos')
    readonly_fields = ('fecha_registro',)
    date_hierarchy  = 'fecha_registro'
    ordering        = ('-fecha_registro',)

    # ── Fieldsets en el formulario de edición ──────────────────────────────────
    fieldsets = (
        ('📋 Identificación', {
            'fields': ('codigo', 'descripcion', 'peso_kg', 'volumen_cm3'),
        }),
        ('👥 Partes involucradas', {
            'fields': ('remitente', 'destinatario', 'ruta', 'empleado_registro'),
        }),
        ('🚚 Estado y fechas', {
            'fields': (
                'estado', 'costo_envio',
                'fecha_registro', 'fecha_entrega_est', 'fecha_entrega_real',
            ),
        }),
        ('📝 Observaciones', {
            'fields': ('observaciones',),
            'classes': ('collapse',),
        }),
    )

    # ── Badge de color para el estado ─────────────────────────────────────────
    @admin.display(description='Estado', ordering='estado')
    def estado_badge(self, obj):
        color, bg = ESTADO_COLORS.get(obj.estado, ('#333', '#eee'))
        label = obj.get_estado_display()
        return format_html(
            '<span style="'
            'display:inline-block;'
            'padding:3px 10px;'
            'border-radius:12px;'
            'font-size:0.82em;'
            'font-weight:600;'
            'color:{};'
            'background-color:{};'
            '">{}</span>',
            color, bg, label,
        )


@admin.register(Empleado)
class EmpleadoAdmin(admin.ModelAdmin):
    list_display  = ('codigo', 'apellidos', 'nombres', 'cargo', 'email', 'estado')
    search_fields = ('codigo', 'apellidos', 'nombres', 'email')
    list_filter   = ('estado', 'cargo')
    fieldsets = (
        ('Datos personales', {
            'fields': ('codigo', 'nombres', 'apellidos', 'cargo'),
        }),
        ('Contacto', {
            'fields': ('email', 'telefono'),
        }),
        ('Asignación', {
            'fields': ('estado', 'fecha_ingreso', 'rutas_asignadas'),
        }),
    )


@admin.register(HistorialEstado)
class HistorialEstadoAdmin(admin.ModelAdmin):
    list_display  = ('encomienda', 'estado_anterior', 'estado_nuevo', 'empleado', 'fecha_cambio')
    readonly_fields = ('fecha_cambio',)
    list_filter   = ('estado_nuevo',)
    search_fields = ('encomienda__codigo',)

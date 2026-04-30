# envios/forms.py
from django import forms
from .models import Encomienda
from clientes.models import Cliente
from rutas.models import Ruta


class EncomiendaForm(forms.ModelForm):
    """
    Formulario para crear y editar encomiendas.
    - Filtra solo clientes activos (estado=1)
    - Filtra solo rutas activas (estado=1)
    - El empleado_registro se asigna desde la vista (usuario logueado)
    """

    class Meta:
        model = Encomienda
        fields = [
            'codigo',
            'descripcion',
            'peso_kg',
            'volumen_cm3',
            'remitente',
            'destinatario',
            'ruta',
            'costo_envio',
            'fecha_entrega_est',
            'observaciones',
        ]
        widgets = {
            'codigo': forms.TextInput(attrs={
                'class': 'form-control',
                'placeholder': 'Ej: ENC-20240101-ABCD12',
            }),
            'descripcion': forms.Textarea(attrs={
                'class': 'form-control',
                'rows': 3,
                'placeholder': 'Describe el contenido del paquete…',
            }),
            'peso_kg': forms.NumberInput(attrs={
                'class': 'form-control',
                'step': '0.01',
                'min': '0.01',
                'placeholder': '0.00',
            }),
            'volumen_cm3': forms.NumberInput(attrs={
                'class': 'form-control',
                'step': '0.01',
                'min': '0',
                'placeholder': '0.00 (opcional)',
            }),
            'remitente': forms.Select(attrs={'class': 'form-select'}),
            'destinatario': forms.Select(attrs={'class': 'form-select'}),
            'ruta': forms.Select(attrs={'class': 'form-select'}),
            'costo_envio': forms.NumberInput(attrs={
                'class': 'form-control',
                'step': '0.01',
                'min': '0',
                'placeholder': '0.00',
            }),
            'fecha_entrega_est': forms.DateInput(attrs={
                'class': 'form-control',
                'type': 'date',
            }),
            'observaciones': forms.Textarea(attrs={
                'class': 'form-control',
                'rows': 2,
                'placeholder': 'Observaciones adicionales (opcional)…',
            }),
        }
        labels = {
            'codigo': 'Código de encomienda',
            'descripcion': 'Descripción del contenido',
            'peso_kg': 'Peso (kg)',
            'volumen_cm3': 'Volumen (cm³)',
            'remitente': 'Remitente',
            'destinatario': 'Destinatario',
            'ruta': 'Ruta de envío',
            'costo_envio': 'Costo de envío (S/.)',
            'fecha_entrega_est': 'Fecha estimada de entrega',
            'observaciones': 'Observaciones',
        }

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        # Solo clientes activos
        self.fields['remitente'].queryset = Cliente.objects.activos().order_by('apellidos')
        self.fields['destinatario'].queryset = Cliente.objects.activos().order_by('apellidos')
        # Solo rutas activas
        self.fields['ruta'].queryset = Ruta.objects.activas().order_by('origen')
        # Campos opcionales
        self.fields['volumen_cm3'].required = False
        self.fields['observaciones'].required = False
        self.fields['fecha_entrega_est'].required = False

    def clean(self):
        cleaned_data = super().clean()
        remitente = cleaned_data.get('remitente')
        destinatario = cleaned_data.get('destinatario')

        if remitente and destinatario and remitente == destinatario:
            self.add_error(
                'destinatario',
                'El destinatario no puede ser el mismo que el remitente.'
            )
        return cleaned_data


class CambiarEstadoForm(forms.Form):
    """Formulario sencillo para cambiar el estado de una encomienda."""
    from config.choices import EstadoEnvio

    nuevo_estado = forms.ChoiceField(
        choices=EstadoEnvio.choices,
        widget=forms.Select(attrs={'class': 'form-select'}),
        label='Nuevo estado',
    )
    observacion = forms.CharField(
        required=False,
        widget=forms.Textarea(attrs={
            'class': 'form-control',
            'rows': 2,
            'placeholder': 'Motivo del cambio de estado (opcional)…',
        }),
        label='Observación',
    )

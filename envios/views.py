# envios/views.py
from django.shortcuts import render, get_object_or_404, redirect
from django.contrib.auth.decorators import login_required
from django.contrib import messages
from django.core.paginator import Paginator
from django.core.exceptions import ValidationError

from config.choices import EstadoEnvio
from .models import Encomienda, Empleado, HistorialEstado
from .forms import EncomiendaForm, CambiarEstadoForm


# ─────────────────────────────────────────────────────────
#  Dashboard
# ─────────────────────────────────────────────────────────

@login_required
def dashboard(request):
    """
    Vista principal: muestra contadores de encomiendas y las últimas 10.
    """
    total_activas   = Encomienda.objects.activas().count()
    total_transito  = Encomienda.objects.en_transito().count()
    total_retraso   = Encomienda.objects.con_retraso().count()
    ultimas         = Encomienda.objects.con_relaciones().order_by('-fecha_registro')[:10]

    context = {
        'total_activas':  total_activas,
        'total_transito': total_transito,
        'total_retraso':  total_retraso,
        'ultimas':        ultimas,
        'EstadoEnvio':    EstadoEnvio,
    }
    return render(request, 'envios/dashboard.html', context)


# ─────────────────────────────────────────────────────────
#  Lista de encomiendas (con paginación y filtro)
# ─────────────────────────────────────────────────────────

@login_required
def lista_encomiendas(request):
    """
    Lista paginada (15 por página) con filtro opcional por estado.
    """
    estado_filtro = request.GET.get('estado', '')
    qs = Encomienda.objects.con_relaciones().order_by('-fecha_registro')

    if estado_filtro:
        qs = qs.filter(estado=estado_filtro)

    paginator = Paginator(qs, 15)
    page_number = request.GET.get('page', 1)
    page_obj = paginator.get_page(page_number)

    context = {
        'page_obj':      page_obj,
        'estado_filtro': estado_filtro,
        'estados':       EstadoEnvio.choices,
        'EstadoEnvio':   EstadoEnvio,
    }
    return render(request, 'envios/lista.html', context)


# ─────────────────────────────────────────────────────────
#  Detalle de encomienda
# ─────────────────────────────────────────────────────────

@login_required
def detalle_encomienda(request, pk):
    """
    Muestra toda la info de la encomienda y su historial de estados.
    """
    encomienda = get_object_or_404(
        Encomienda.objects.con_relaciones().prefetch_related('historial__empleado'),
        pk=pk,
    )
    historial = encomienda.historial.order_by('-fecha_cambio')
    form_estado = CambiarEstadoForm()

    context = {
        'encomienda':  encomienda,
        'historial':   historial,
        'form_estado': form_estado,
        'EstadoEnvio': EstadoEnvio,
    }
    return render(request, 'envios/detalle.html', context)


# ─────────────────────────────────────────────────────────
#  Crear encomienda
# ─────────────────────────────────────────────────────────

@login_required
def crear_encomienda(request):
    """
    Formulario de nueva encomienda. El empleado_registro se asigna
    automáticamente al Empleado cuyo email coincide con el usuario logueado,
    o al primero disponible si no coincide.
    """
    if request.method == 'POST':
        form = EncomiendaForm(request.POST)
        if form.is_valid():
            try:
                encomienda = form.save(commit=False)
                # Asignar empleado_registro al usuario logueado
                try:
                    empleado = Empleado.objects.get(email=request.user.email)
                except Empleado.DoesNotExist:
                    empleado = Empleado.objects.first()

                if not empleado:
                    messages.error(
                        request,
                        'No existe ningún empleado registrado. '
                        'Crea uno en el Admin antes de registrar encomiendas.'
                    )
                    return render(request, 'envios/form.html', {'form': form})

                encomienda.empleado_registro = empleado
                encomienda.save()
                messages.success(
                    request,
                    f'✅ Encomienda {encomienda.codigo} creada exitosamente.'
                )
                return redirect('detalle', pk=encomienda.pk)
            except ValidationError as e:
                messages.error(request, f'Error de validación: {e.message}')
        else:
            messages.error(
                request,
                '❌ Por favor corrige los errores del formulario.'
            )
    else:
        form = EncomiendaForm()

    return render(request, 'envios/form.html', {'form': form, 'accion': 'Crear'})


# ─────────────────────────────────────────────────────────
#  Cambiar estado de encomienda
# ─────────────────────────────────────────────────────────

@login_required
def cambiar_estado_encomienda(request, pk):
    """
    Cambia el estado de una encomienda y registra el historial.
    Solo acepta POST.
    """
    encomienda = get_object_or_404(Encomienda, pk=pk)

    if request.method == 'POST':
        form = CambiarEstadoForm(request.POST)
        if form.is_valid():
            nuevo_estado = form.cleaned_data['nuevo_estado']
            observacion  = form.cleaned_data.get('observacion', '')

            try:
                empleado = Empleado.objects.get(email=request.user.email)
            except Empleado.DoesNotExist:
                empleado = Empleado.objects.first()

            if not empleado:
                messages.error(request, 'No hay empleados registrados para registrar el cambio.')
                return redirect('detalle', pk=pk)

            try:
                encomienda.cambiar_estado(nuevo_estado, empleado=empleado, observacion=observacion)
                messages.success(
                    request,
                    f'✅ Estado actualizado a "{encomienda.get_estado_display()}" correctamente.'
                )
            except ValueError as e:
                messages.warning(request, str(e))

    return redirect('detalle', pk=pk)

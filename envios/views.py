# envios/views.py
from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth.decorators import login_required
from django.contrib import messages
from django.core.paginator import Paginator
from django.utils import timezone

from config.choices import EstadoEnvio
from .models import Encomienda, Empleado, HistorialEstado
from .forms import EncomiendaForm, CambiarEstadoForm
# Sesión 07: notificaciones WebSocket desde la vista síncrona
from .async_services import notify_dashboard_update, notify_encomienda_update, notify_activity


# ─────────────────────────────────────────────────────────
#  Dashboard
# ─────────────────────────────────────────────────────────

@login_required
def dashboard(request):
    """Vista principal del sistema con estadísticas"""
    hoy = timezone.now().date()
    context = {
        'total_activas':   Encomienda.objects.activas().count(),
        'en_transito':     Encomienda.objects.en_transito().count(),
        'con_retraso':     Encomienda.objects.con_retraso().count(),
        'entregadas_hoy':  Encomienda.objects.filter(
                               estado=EstadoEnvio.ENTREGADO,
                               fecha_entrega_real=hoy
                           ).count(),
        'ultimas':         Encomienda.objects.con_relaciones()[:5],
        'EstadoEnvio':     EstadoEnvio,
    }
    return render(request, 'envios/dashboard.html', context)


# ─────────────────────────────────────────────────────────
#  Lista de encomiendas (paginación + filtro)
# ─────────────────────────────────────────────────────────

@login_required
def encomienda_lista(request):
    """Lista paginada (15/pág) con filtro opcional por estado."""
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
def encomienda_detalle(request, pk):
    """Muestra toda la info de la encomienda y su historial de estados."""
    encomienda = get_object_or_404(
        Encomienda.objects.con_relaciones().prefetch_related('historial__empleado'),
        pk=pk,
    )
    historial    = encomienda.historial.order_by('-fecha_cambio')
    form_estado  = CambiarEstadoForm()

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
def encomienda_crear(request):
    """
    GET  → muestra el formulario vacío
    POST → valida, guarda y redirige al detalle
    El empleado_registro se asigna por email del usuario logueado.
    """
    if request.method == 'POST':
        form = EncomiendaForm(request.POST)
        if form.is_valid():
            try:
                enc = form.save(commit=False)
                enc.empleado_registro = Empleado.objects.get(
                    email=request.user.email
                )
                enc.save()
                messages.success(
                    request,
                    f'Encomienda {enc.codigo} registrada correctamente.'
                )
                # Patrón PRG: redirige para evitar reenvío
                return redirect('encomienda_detalle', pk=enc.pk)
            except Empleado.DoesNotExist:
                messages.error(
                    request,
                    f'No existe un Empleado con el email "{request.user.email}". '
                    'Crea el empleado en el Admin con ese email antes de registrar encomiendas.'
                )
        else:
            messages.error(request, 'Por favor corrige los errores del formulario.')
    else:
        form = EncomiendaForm()

    return render(request, 'envios/form.html', {
        'form':   form,
        'titulo': 'Nueva Encomienda',
    })


# ─────────────────────────────────────────────────────────
#  Cambiar estado de encomienda
# ─────────────────────────────────────────────────────────

@login_required
def encomienda_cambiar_estado(request, pk):
    """Cambia el estado y registra en el historial. Solo acepta POST."""
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
                return redirect('encomienda_detalle', pk=pk)

            try:
                encomienda.cambiar_estado(
                    nuevo_estado, empleado=empleado, observacion=observacion
                )
                messages.success(
                    request,
                    f'Estado actualizado a "{encomienda.get_estado_display()}" correctamente.'
                )
                # Sesión 07: notificar vía WebSocket
                notify_encomienda_update(encomienda.pk)
                notify_dashboard_update()
                notify_activity(
                    f'Encomienda {encomienda.codigo} cambió a "{encomienda.get_estado_display()}"',
                    usuario=request.user.username,
                )
            except ValueError as e:
                messages.warning(request, str(e))

    return redirect('encomienda_detalle', pk=pk)

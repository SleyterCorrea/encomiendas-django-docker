from django.shortcuts import render
from .models import Encomienda


def inicio(request):
    encomiendas = Encomienda.objects.all()[:10]
    return render(request, 'envios/inicio.html', {'encomiendas': encomiendas})

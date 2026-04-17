from django.db import models


class Cliente(models.Model):
    nombres = models.CharField(max_length=120)
    apellidos = models.CharField(max_length=120)
    telefono = models.CharField(max_length=20, blank=True)
    correo = models.EmailField(unique=True)
    direccion = models.CharField(max_length=255, blank=True)
    creado_en = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return f"{self.nombres} {self.apellidos}".strip()

from django.db import models


class Ruta(models.Model):
    origen = models.CharField(max_length=120)
    destino = models.CharField(max_length=120)
    distancia_km = models.DecimalField(max_digits=8, decimal_places=2)
    activa = models.BooleanField(default=True)

    def __str__(self):
        return f"{self.origen} → {self.destino}"

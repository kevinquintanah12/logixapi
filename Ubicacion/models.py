# ubicacion/models.py
from django.db import models

class Ubicacion(models.Model):
    ciudad = models.CharField(max_length=255)
    estado = models.CharField(max_length=255)
    latitud = models.DecimalField(max_digits=10, decimal_places=6)
    longitud = models.DecimalField(max_digits=10, decimal_places=6)

    def __str__(self):
        return f"{self.ciudad}, {self.estado}"

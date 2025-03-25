# centro_distribucion/models.py
from django.db import models
from Ubicacion.models import Ubicacion

class CentroDistribucion(models.Model):
    ubicacion = models.OneToOneField(Ubicacion, on_delete=models.CASCADE)
    nombre = models.CharField(max_length=255)

    def __str__(self):
        return f"Centro de Distribución: {self.nombre} - {self.ubicacion}"

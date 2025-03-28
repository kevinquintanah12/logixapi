from django.db import models

class Camion(models.Model):
    matricula = models.CharField(max_length=255, unique=True)
    marca = models.CharField(max_length=255)
    modelo = models.CharField(max_length=255)
    capacidad_carga = models.FloatField()
    tipo_vehiculo = models.CharField(max_length=255)
    cumplimiento_normas = models.BooleanField()

    def __str__(self):
        return f"{self.marca} {self.modelo} ({self.matricula})"

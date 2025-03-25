from django.db import models

class Destinatario(models.Model):
    rfc = models.CharField(max_length=13, null=True, blank=True)  # Permitir que sea nulo
    nombre = models.CharField(max_length=255)
    apellidos = models.CharField(max_length=255)
    correo_electronico = models.CharField(max_length=255, null=True, blank=True)
    telefono = models.CharField(max_length=20, null=True, blank=True)
    pin = models.CharField(max_length=6, null=True, blank=True)
    direccion_detallada = models.TextField()
    calle = models.CharField(max_length=255)
    colonia = models.CharField(max_length=255)
    numero = models.CharField(max_length=10)
    ciudad = models.CharField(max_length=255)
    estado = models.CharField(max_length=255)
    codigo_postal = models.CharField(max_length=10)

    def __str__(self):
        return f"{self.nombre} {self.apellidos}"

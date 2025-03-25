from django.db import models

class Cliente(models.Model):
    nombre = models.CharField(max_length=255)
    apellido = models.CharField(max_length=255)
    razon_social = models.CharField(max_length=255, null=True, blank=True)
    rfc = models.CharField(max_length=13)
    direccion = models.TextField()
    codigo_postal = models.CharField(max_length=10)
    telefono = models.CharField(max_length=20, null=True, blank=True)
    email = models.CharField(max_length=255, null=True, blank=True)
    fecha_registro = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return f"{self.nombre} {self.apellido}"

from django.db import models
from django.contrib.auth.models import User
from horarios.models import Horario

class Chofer(models.Model):
    usuario = models.OneToOneField(User, on_delete=models.CASCADE)
    nombre = models.CharField(max_length=100)
    apellidos = models.CharField(max_length=100)
    rfc = models.CharField(max_length=13)
    licencia = models.CharField(max_length=50)
    certificaciones = models.TextField(blank=True, null=True)
    horario = models.ForeignKey(Horario, on_delete=models.SET_NULL, null=True)
    pin = models.CharField(max_length=4, blank=True, null=True)  # Se guarda el PIN, 4 dígitos

    def __str__(self):
        return f"{self.nombre} {self.apellidos}"

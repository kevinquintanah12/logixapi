from django.db import models
from django.contrib.auth.models import User
from horarios.models import Horario

class Chofer(models.Model):
    nombre = models.CharField(max_length=255)
    apellidos = models.CharField(max_length=255)
    usuario = models.OneToOneField(User, on_delete=models.CASCADE)
    rfc = models.CharField(max_length=255, unique=True)
    licencia = models.CharField(max_length=255, unique=True)
    certificaciones = models.TextField(null=True, blank=True)
    horario = models.ForeignKey(Horario, on_delete=models.CASCADE)
    pin = models.CharField(max_length=4, null=True, blank=True)  # Ahora puede ser nulo

    def __str__(self):
        return f"{self.nombre} {self.apellidos}"

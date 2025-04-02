import random
import string
from django.db import models
from destinatario.models import Destinatario
from paquete.models import Paquete  # Ahora importamos Paquete desde paquete.models

# Modelo Entrega
class Entrega(models.Model):  # Heredamos de Paquete
    paquete = models.ForeignKey(Paquete, on_delete=models.CASCADE)
    destinatario = models.ForeignKey(Destinatario, null=True, blank=True, on_delete=models.SET_NULL)
    fecha_entrega = models.DateTimeField()
    estado = models.CharField(max_length=50)
    pin = models.CharField(max_length=50)
    fecha_registro = models.DateTimeField(auto_now_add=True)
    notificacion_enviada = models.BooleanField(default=False)
    fecha_notificacion = models.DateTimeField(null=True, blank=True)

    def __str__(self):
        return f"Entrega {self.numero_guia} - Estado {self.estado}"

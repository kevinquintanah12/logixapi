from django.db import models
from calcularenvio.models import CalcularEnvio  # Asegúrate de importar correctamente CalcularEnvio
from destinatario.models import Destinatario  # Ajusta según la ubicación de tu modelo
from cliente.models import Cliente  # Ajusta según la ubicación de tu modelo


class Producto(models.Model):
    description = models.TextField()
    codigosat = models.CharField(max_length=255)
    noidentificacion = models.CharField(max_length=255)
    codigobarras = models.CharField(max_length=255, null=True, blank=True)
    
    destinatario = models.ForeignKey(Destinatario, on_delete=models.CASCADE)
    cliente = models.ForeignKey(Cliente, on_delete=models.CASCADE)
    calculoenvio = models.ForeignKey(CalcularEnvio, on_delete=models.CASCADE)  # Relación con CalcularEnvio

    def __str__(self):
        return f"Producto {self.id} - {self.description}"

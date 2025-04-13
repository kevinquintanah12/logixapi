from django.db import models
from rutas.models import Ruta  # Importa tu modelo de Ruta

class SensorRuta(models.Model):
    ruta = models.ForeignKey(Ruta, on_delete=models.CASCADE, related_name='sensores')
    latitud = models.DecimalField(max_digits=9, decimal_places=6)
    longitud = models.DecimalField(max_digits=9, decimal_places=6)
    temperatura = models.FloatField()
    humedad = models.FloatField()
    timestamp = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return f"Sensor ({self.ruta.entregas.paquete.numero_guia}) - {self.timestamp}"

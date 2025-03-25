from django.db import models
from Ubicacion.models import Ubicacion
from tipoproductos.models import TipoProducto
from centrodistribucion.models import CentroDistribucion

class CalcularEnvio(models.Model):
    tipo_producto = models.ForeignKey(TipoProducto, on_delete=models.CASCADE)
    origen_cd = models.ForeignKey(CentroDistribucion, on_delete=models.CASCADE)
    destino = models.ForeignKey(Ubicacion, on_delete=models.CASCADE)

    peso_unitario = models.DecimalField(max_digits=10, decimal_places=2)
    numero_piezas = models.IntegerField()
    
    dimensiones_largo = models.DecimalField(max_digits=10, decimal_places=2)
    dimensiones_ancho = models.DecimalField(max_digits=10, decimal_places=2)
    dimensiones_alto = models.DecimalField(max_digits=10, decimal_places=2)
    
    tarifa_base = models.DecimalField(max_digits=10, decimal_places=2)
    tarifa_extra_temperatura = models.DecimalField(max_digits=10, decimal_places=2, default=0)
    tarifa_extra_humedad = models.DecimalField(max_digits=10, decimal_places=2, default=0)
    
    trasladoiva = models.DecimalField(max_digits=10, decimal_places=2)
    ieps = models.DecimalField(max_digits=10, decimal_places=2)
    
    # Nuevos campos para los cálculos
    descripcion = models.TextField()
    tarifa_por_kg = models.DecimalField(max_digits=10, decimal_places=2, null=True, blank=True)
    tarifa_por_km = models.DecimalField(max_digits=10, decimal_places=2, null=True, blank=True)
    tarifa_peso = models.DecimalField(max_digits=10, decimal_places=2, null=True, blank=True)
    distancia_km = models.DecimalField(max_digits=10, decimal_places=2, null=True, blank=True)
    total_tarifa = models.DecimalField(max_digits=10, decimal_places=2, null=True, blank=True)

    # Nuevo campo para Envío Express
    envio_express = models.BooleanField(default=False)

    def __str__(self):
        return f"Envio {self.id} - {self.descripcion}"

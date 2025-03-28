from django.db import models
from chofer.models import Chofer
from camiones.models import Camion
from entrega.models import Entrega  # Importa Entrega para hacer la referencia

class Ruta(models.Model):
   
    distancia = models.FloatField()
    prioridad = models.IntegerField()
    conductor = models.ForeignKey(Chofer, on_delete=models.CASCADE)
    vehiculo = models.ForeignKey(Camion, on_delete=models.CASCADE)
    fecha_inicio = models.DateTimeField()
    fecha_fin = models.DateTimeField()
    estado = models.CharField(max_length=50, default="por hacer")
    
    # Relación inversa con Entrega
    entregas = models.ForeignKey(Entrega, on_delete=models.SET_NULL, null=True, blank=True, related_name="rutas")

    def __str__(self):
        return f"Ruta de {self.ruta_origen} a {self.ruta_destino}"

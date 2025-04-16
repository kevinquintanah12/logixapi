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
    
    # Cambiado a ManyToManyField para permitir agregar entregas usando .add()
    entregas = models.ManyToManyField(Entrega, blank=True, related_name="rutas")

    def __str__(self):
        # Asegúrate de reemplazar "ruta_origen" y "ruta_destino" con campos válidos o usa otro identificador.
        return f"Ruta {self.id} - {self.estado}"

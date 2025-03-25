import random
import string
from django.db import models
from producto.models import Producto  # Asegúrate de importar correctamente el modelo Producto

def generar_numero_guia():
    # Función para generar un número de guía aleatorio
    return ''.join(random.choices(string.ascii_uppercase + string.digits, k=10))

def generar_codigo_barras():
    # Función para generar un código de barras aleatorio
    return ''.join(random.choices(string.digits, k=13))

class Paquete(models.Model):
    producto = models.ForeignKey(Producto, on_delete=models.CASCADE)
    numero_guia = models.CharField(max_length=255, default=generar_numero_guia)
    codigo_barras = models.CharField(max_length=255, null=True, blank=True, default=generar_codigo_barras)
    fecha_registro = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return f"Paquete {self.numero_guia} - Producto {self.producto.id}"

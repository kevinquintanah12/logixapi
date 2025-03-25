from django.db import models

class TipoProducto(models.Model):
    nombre = models.CharField(max_length=255)
    descripcion = models.TextField()
    precio_base = models.DecimalField(max_digits=10, decimal_places=2)

    def __str__(self):
        return self.nombre

class Temperatura(models.Model):
    tipo_producto = models.OneToOneField(TipoProducto, on_delete=models.CASCADE, related_name="temperatura")
    rango_minimo = models.IntegerField()
    rango_maximo = models.IntegerField()
    tarifa_extra = models.DecimalField(max_digits=10, decimal_places=2, default=0)

    def __str__(self):
        return f"Temp {self.rango_minimo}-{self.rango_maximo}°C"

class Humedad(models.Model):
    tipo_producto = models.OneToOneField(TipoProducto, on_delete=models.CASCADE, related_name="humedad")
    rango_minimo = models.IntegerField()
    rango_maximo = models.IntegerField()
    tarifa_extra = models.DecimalField(max_digits=10, decimal_places=2, default=0)

    def __str__(self):
        return f"Humedad {self.rango_minimo}-{self.rango_maximo}%"

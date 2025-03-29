import requests
from django.db import models
from decimal import Decimal

class Ubicacion(models.Model):
    ciudad = models.CharField(max_length=255)
    estado = models.CharField(max_length=255)
    latitud = models.DecimalField(max_digits=10, decimal_places=6, null=True, blank=True)
    longitud = models.DecimalField(max_digits=10, decimal_places=6, null=True, blank=True)

    MAPBOX_ACCESS_TOKEN = "pk.eyJ1IjoiZGF5a2V2MTIiLCJhIjoiY204MTd5NzR3MGdxYTJqcGlsa29odnQ5YiJ9.tbAEt453VxfJoDatpU72YQ"

    def obtener_coordenadas(self):
        """Obtiene la latitud y longitud a partir de la ciudad y el estado usando la API de Mapbox"""
        direccion = f"{self.ciudad}, {self.estado}"
        url = f"https://api.mapbox.com/geocoding/v5/mapbox.places/{direccion}.json?access_token={self.MAPBOX_ACCESS_TOKEN}"
        
        response = requests.get(url)
        if response.status_code == 200:
            data = response.json()
            if data["features"]:
                self.longitud, self.latitud = data["features"][0]["geometry"]["coordinates"]
            else:
                raise Exception("No se encontraron coordenadas para la ubicación proporcionada.")

    def save(self, *args, **kwargs):
        """Sobreescribe save para obtener coordenadas antes de guardar si no están definidas"""
        if not self.latitud or not self.longitud:
            self.obtener_coordenadas()
        super().save(*args, **kwargs)

    def __str__(self):
        return f"{self.ciudad}, {self.estado}"

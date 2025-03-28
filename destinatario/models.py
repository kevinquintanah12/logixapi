from django.db import models
import requests

class Destinatario(models.Model):
    rfc = models.CharField(max_length=13, null=True, blank=True)
    nombre = models.CharField(max_length=255)
    apellidos = models.CharField(max_length=255)
    correo_electronico = models.CharField(max_length=255, null=True, blank=True)
    telefono = models.CharField(max_length=20, null=True, blank=True)
    pin = models.CharField(max_length=6, null=True, blank=True)
    direccion_detallada = models.TextField()
    calle = models.CharField(max_length=255)
    colonia = models.CharField(max_length=255)
    numero = models.CharField(max_length=10)
    ciudad = models.CharField(max_length=255)
    estado = models.CharField(max_length=255)
    codigo_postal = models.CharField(max_length=10)
    latitud = models.FloatField(null=True, blank=True)
    longitud = models.FloatField(null=True, blank=True)

    MAPBOX_ACCESS_TOKEN = "pk.eyJ1IjoiZGF5a2V2MTIiLCJhIjoiY204MTd5NzR3MGdxYTJqcGlsa29odnQ5YiJ9.tbAEt453VxfJoDatpU72YQ"

    def obtener_coordenadas(self):
        """Obtiene las coordenadas de la dirección usando la API de Mapbox"""
        direccion = f"{self.calle} {self.numero}, {self.colonia}, {self.ciudad}, {self.estado}, {self.codigo_postal}"
        url = f"https://api.mapbox.com/geocoding/v5/mapbox.places/{direccion}.json?access_token={self.MAPBOX_ACCESS_TOKEN}"
        
        response = requests.get(url)
        if response.status_code == 200:
            data = response.json()
            if data["features"]:
                self.longitud, self.latitud = data["features"][0]["geometry"]["coordinates"]
                self.save()

    def save(self, *args, **kwargs):
        """Sobreescribimos save para obtener coordenadas antes de guardar"""
        if not self.latitud or not self.longitud:
            self.obtener_coordenadas()
        super().save(*args, **kwargs)

    def __str__(self):
        return f"{self.nombre} {self.apellidos}"

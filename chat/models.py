from django.db import models

class Mensaje(models.Model):
    nombre = models.CharField(max_length=100, blank=True, null=True)  # opcional
    contenido = models.TextField()
    timestamp = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return f"{self.nombre or 'Anónimo'}: {self.contenido[:30]}"

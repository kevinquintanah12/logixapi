from django.db import models

class Horario(models.Model):
    nombre = models.CharField(max_length=255)  # Ejemplo: "Turno Matutino"
    hora_inicio = models.TimeField()
    hora_fin = models.TimeField()

    def __str__(self):
        return self.nombre

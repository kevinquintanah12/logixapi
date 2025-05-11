from django.db import models

class Mensaje(models.Model):
    remitente    = models.CharField(max_length=100)
    destinatario = models.CharField(max_length=100)
    contenido    = models.TextField()
    timestamp    = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return f"{self.timestamp} | {self.remitente} → {self.destinatario}: {self.contenido[:20]}"

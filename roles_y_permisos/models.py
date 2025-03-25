from django.db import models
from django.conf import settings  # Para usar AUTH_USER_MODEL

# Modelo para Roles
class Rol(models.Model):
    nombre = models.CharField(max_length=255, unique=True)

    def __str__(self):
        return self.nombre

# Modelo para Permisos
class Permiso(models.Model):
    nombre = models.CharField(max_length=255, unique=True)
    descripcion = models.TextField()

    def __str__(self):
        return self.nombre

# Relación entre Roles y Permisos (muchos a muchos)
class RolPermiso(models.Model):
    rol = models.ForeignKey(Rol, on_delete=models.CASCADE)
    permiso = models.ForeignKey(Permiso, on_delete=models.CASCADE)

    def __str__(self):
        return f'{self.rol.nombre} - {self.permiso.nombre}'

# Relación entre Usuarios y Roles
class UsuarioRol(models.Model):
    usuario = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE)
    rol = models.ForeignKey(Rol, on_delete=models.SET_NULL, null=True)

    class Meta:
        unique_together = ('usuario', 'rol')  # Un usuario solo puede tener un rol específico una vez

    def __str__(self):
        return f'{self.usuario.username} - {self.rol.nombre}'

# Modelo de ejemplo donde usamos el modelo de usuario configurado en settings.AUTH_USER_MODEL
class Ejemplo(models.Model):
    posted_by = models.ForeignKey(settings.AUTH_USER_MODEL, null=True, on_delete=models.CASCADE)

    def __str__(self):
        return f'{self.posted_by.username}'

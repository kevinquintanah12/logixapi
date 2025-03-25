from django.contrib.auth import get_user_model
import graphene
from graphene_django import DjangoObjectType
from .models import Rol, Permiso, RolPermiso, UsuarioRol
from graphql_jwt.decorators import login_required

# Tipos de GraphQL para los modelos

class RolType(DjangoObjectType):
    class Meta:
        model = Rol

class PermisoType(DjangoObjectType):
    class Meta:
        model = Permiso

class RolPermisoType(DjangoObjectType):
    class Meta:
        model = RolPermiso

class UsuarioRolType(DjangoObjectType):
    class Meta:
        model = UsuarioRol


# Mutaciones

class CrearRol(graphene.Mutation):
    class Arguments:
        nombre = graphene.String(required=True)

    rol = graphene.Field(RolType)

    def mutate(self, info, nombre):
        rol = Rol.objects.create(nombre=nombre)
        return CrearRol(rol=rol)


class CrearPermiso(graphene.Mutation):
    class Arguments:
        nombre = graphene.String(required=True)
        descripcion = graphene.String(required=True)

    permiso = graphene.Field(PermisoType)

    def mutate(self, info, nombre, descripcion):
        permiso = Permiso.objects.create(nombre=nombre, descripcion=descripcion)
        return CrearPermiso(permiso=permiso)


class AsignarPermisoARol(graphene.Mutation):
    class Arguments:
        rol_id = graphene.Int(required=True)
        permiso_id = graphene.Int(required=True)

    rol_permiso = graphene.Field(RolPermisoType)

    def mutate(self, info, rol_id, permiso_id):
        rol = Rol.objects.get(id=rol_id)
        permiso = Permiso.objects.get(id=permiso_id)
        rol_permiso = RolPermiso.objects.create(rol=rol, permiso=permiso)
        return AsignarPermisoARol(rol_permiso=rol_permiso)


# Asignar Rol a un Usuario autenticado
class AsignarRolAUsuario(graphene.Mutation):
    class Arguments:
        rol_id = graphene.Int(required=True)
        usuario_id = graphene.Int(required=True)  # ID del usuario al que asignar el rol

    usuario_rol = graphene.Field(UsuarioRolType)

    @login_required  # Este decorador asegura que el usuario esté autenticado
    def mutate(self, info, rol_id, usuario_id):
        try:
            # Obtener el rol por ID
            rol = Rol.objects.get(id=rol_id)
        except Rol.DoesNotExist:
            raise Exception("Rol no encontrado")

        try:
            # Obtener el usuario por ID usando get_user_model() en lugar de settings.AUTH_USER_MODEL
            usuario = get_user_model().objects.get(id=usuario_id)
        except get_user_model().DoesNotExist:
            raise Exception("Usuario no encontrado")

        # Asignar el rol al usuario
        usuario_rol = UsuarioRol.objects.create(usuario=usuario, rol=rol)

        return AsignarRolAUsuario(usuario_rol=usuario_rol)


# Consultas

class Query(graphene.ObjectType):
    roles = graphene.List(RolType)
    permisos = graphene.List(PermisoType)
    usuarios_roles = graphene.List(UsuarioRolType)  # Consulta para obtener roles asignados a usuarios

    def resolve_roles(self, info):
        return Rol.objects.all()

    def resolve_permisos(self, info):
        return Permiso.objects.all()

    def resolve_usuarios_roles(self, info):
        return UsuarioRol.objects.all()


# Mutaciones

class Mutation(graphene.ObjectType):
    crear_rol = CrearRol.Field()
    crear_permiso = CrearPermiso.Field()
    asignar_permiso_a_rol = AsignarPermisoARol.Field()
    asignar_rol_a_usuario = AsignarRolAUsuario.Field()


# Esquema

schema = graphene.Schema(query=Query, mutation=Mutation)

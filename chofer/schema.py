import graphene
from graphene_django.types import DjangoObjectType
from .models import Chofer
from horarios.models import Horario
from horarios.schema import HorarioType
from django.contrib.auth.models import User

# Función para verificar si un PIN es secuencial

def es_secuencial(pin):
    ascending  = all(int(pin[i]) + 1 == int(pin[i+1]) for i in range(len(pin) - 1))
    descending = all(int(pin[i]) - 1 == int(pin[i+1]) for i in range(len(pin) - 1))
    return ascending or descending

# Tipo GraphQL para el modelo Chofer
class ChoferType(DjangoObjectType):
    class Meta:
        model = Chofer

# Definición de consultas GraphQL
class Query(graphene.ObjectType):
    all_choferes       = graphene.List(ChoferType)
    chofer_by_id       = graphene.Field(ChoferType, id=graphene.Int())
    chofer_autenticado = graphene.Field(ChoferType)
    check_pin          = graphene.Boolean(pin=graphene.String(required=True))

    def resolve_all_choferes(self, info, **kwargs):
        user = info.context.user
        if not user.is_authenticated:
            raise Exception("Debes estar autenticado para ver la lista de choferes.")
        return Chofer.objects.all()

    def resolve_chofer_by_id(self, info, id):
        user = info.context.user
        if not user.is_authenticated:
            raise Exception("Debes estar autenticado para ver los detalles de un chofer.")
        return Chofer.objects.filter(pk=id).first()

    def resolve_chofer_autenticado(self, info):
        user = info.context.user
        if not user.is_authenticated:
            raise Exception("Debes estar autenticado para ver tu información.")
        return Chofer.objects.filter(usuario=user).first()

    def resolve_check_pin(self, info, pin):
        user = info.context.user
        if not user.is_authenticated:
            raise Exception("Debes estar autenticado para verificar el PIN.")
        chofer = Chofer.objects.filter(usuario=user).first()
        if not chofer:
            raise Exception("No se encontró un chofer asociado a tu cuenta.")
        return chofer.pin == pin

# Mutación para crear un Chofer (sin correo ni user creation)
class CreateChofer(graphene.Mutation):
    class Arguments:
        user_id         = graphene.Int(required=True)
        nombre          = graphene.String(required=True)
        apellidos       = graphene.String(required=True)
        rfc             = graphene.String(required=True)
        licencia        = graphene.String(required=True)
        certificaciones = graphene.String()
        horario_id      = graphene.Int(required=True)
        password        = graphene.String(required=True)

    chofer = graphene.Field(ChoferType)

    def mutate(self, info, user_id, nombre, apellidos, rfc, licencia, certificaciones, horario_id, password):
        # Buscar el usuario
        try:
            usuario = User.objects.get(id=user_id)
        except User.DoesNotExist:
            raise Exception("El usuario especificado no existe.")

        # Asignar y guardar contraseña cifrada
        usuario.set_password(password)
        usuario.save()

        # Verificar horario
        try:
            horario = Horario.objects.get(id=horario_id)
        except Horario.DoesNotExist:
            raise Exception("El horario especificado no existe.")

        # Crear chofer
        chofer = Chofer(
            nombre          = nombre,
            apellidos       = apellidos,
            usuario         = usuario,
            rfc             = rfc,
            licencia        = licencia,
            certificaciones = certificaciones,
            horario         = horario,
            pin             = None
        )
        chofer.save()

        return CreateChofer(chofer=chofer)

# Mutación para establecer PIN del chofer
class SetChoferPin(graphene.Mutation):
    class Arguments:
        pin = graphene.String(required=True)

    chofer = graphene.Field(ChoferType)

    def mutate(self, info, pin):
        user = info.context.user
        if not user.is_authenticated:
            raise Exception("Debes estar autenticado para establecer un PIN.")
        chofer = Chofer.objects.filter(usuario=user).first()
        if not chofer:
            raise Exception("No tienes permiso para establecer un PIN.")
        if not pin.isdigit() or len(pin) != 4:
            raise Exception("El PIN debe contener exactamente 4 dígitos numéricos.")
        if es_secuencial(pin):
            raise Exception("El PIN no puede ser una secuencia numérica.")
        chofer.pin = pin
        chofer.save()
        return SetChoferPin(chofer=chofer)

# Mutación para actualizar PIN validando el actual
class UpdateChoferPin(graphene.Mutation):
    class Arguments:
        old_pin = graphene.String(required=True)
        new_pin = graphene.String(required=True)

    chofer = graphene.Field(ChoferType)

    def mutate(self, info, old_pin, new_pin):
        user = info.context.user
        if not user.is_authenticated:
            raise Exception("Debes estar autenticado para editar el PIN.")
        chofer = Chofer.objects.filter(usuario=user).first()
        if not chofer:
            raise Exception("No tienes permiso para editar el PIN.")
        if chofer.pin != old_pin:
            raise Exception("El PIN actual no coincide.")
        if not new_pin.isdigit() or len(new_pin) != 4:
            raise Exception("El nuevo PIN debe contener exactamente 4 dígitos numéricos.")
        if es_secuencial(new_pin):
            raise Exception("El nuevo PIN no puede ser una secuencia numérica.")
        chofer.pin = new_pin
        chofer.save()
        return UpdateChoferPin(chofer=chofer)

# Mutación para actualizar datos del chofer
class ActualizarChofer(graphene.Mutation):
    class Arguments:
        id              = graphene.Int(required=True)
        nombre          = graphene.String(required=True)
        apellidos       = graphene.String(required=True)
        rfc             = graphene.String(required=True)
        licencia        = graphene.String(required=True)
        certificaciones = graphene.String()

    chofer = graphene.Field(ChoferType)

    def mutate(self, info, id, nombre, apellidos, rfc, licencia, certificaciones):
        user = info.context.user
        if not user.is_authenticated:
            raise Exception("Debes estar autenticado para actualizar choferes.")
        try:
            chofer = Chofer.objects.get(pk=id)
        except Chofer.DoesNotExist:
            raise Exception("Chofer no encontrado.")
        chofer.nombre          = nombre
        chofer.apellidos       = apellidos
        chofer.rfc             = rfc
        chofer.licencia        = licencia
        chofer.certificaciones = certificaciones
        chofer.save()
        return ActualizarChofer(chofer=chofer)

# Mutación para eliminar chofer
class EliminarChofer(graphene.Mutation):
    class Arguments:
        id = graphene.Int(required=True)

    ok = graphene.Boolean()

    def mutate(self, info, id):
        user = info.context.user
        if not user.is_authenticated:
            raise Exception("Debes estar autenticado para eliminar choferes.")
        try:
            chofer = Chofer.objects.get(pk=id)
        except Choфер.DoesNotExist:
            raise Exception("Chofer no encontrado.")
        chofer.delete()
        return EliminarChofer(ok=True)

# Definición de Mutaciones
class Mutation(graphene.ObjectType):
    create_chofer      = CreateChofer.Field()
    set_chofer_pin     = SetChoferPin.Field()
    update_chofer_pin  = UpdateChoferPin.Field()
    actualizar_chofer  = ActualizarChofer.Field()
    eliminar_chofer    = EliminarChofer.Field()

# Esquema final
schema = graphene.Schema(query=Query, mutation=Mutation)

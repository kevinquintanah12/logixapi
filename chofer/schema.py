import graphene
import graphql_jwt
from django.contrib.auth import get_user_model
from graphene_django.types import DjangoObjectType
from .models import Chofer
from horarios.models import Horario
from horarios.schema import HorarioType

User = get_user_model()

# Función para verificar si un PIN es secuencial
def es_secuencial(pin):
    ascending = all(int(pin[i]) + 1 == int(pin[i+1]) for i in range(len(pin) - 1))
    descending = all(int(pin[i]) - 1 == int(pin[i+1]) for i in range(len(pin) - 1))
    return ascending or descending

# --- GraphQL Types ---
class ChoferType(DjangoObjectType):
    class Meta:
        model = Chofer

class UserType(DjangoObjectType):
    chofer = graphene.Field(ChoferType)

    class Meta:
        model = User
        exclude = ('password',)

    def resolve_chofer(self, info):
        return Chofer.objects.filter(usuario=self).first()

# --- Auth Mutation: TokenAuthDriver ---
class TokenAuthDriver(graphql_jwt.ObtainJSONWebToken):
    user   = graphene.Field(UserType)
    chofer = graphene.Field(ChoferType)

    @classmethod
    def resolve(cls, root, info, **kwargs):
        user = info.context.user
        return cls(
            token=getattr(root, 'token', None),
            payload=getattr(root, 'payload', None),
            user=user,
            chofer=Chofer.objects.filter(usuario=user).first()
        )

# --- Chofer Queries ---
class Query(graphene.ObjectType):
    all_choferes       = graphene.List(ChoferType)
    chofer_by_id       = graphene.Field(ChoferType, id=graphene.Int())
    chofer_autenticado = graphene.Field(ChoferType)
    check_pin          = graphene.Boolean(pin=graphene.String(required=True))

    def resolve_all_choferes(self, info, **kwargs):
        return Chofer.objects.all()

    def resolve_chofer_by_id(self, info, id):
        return Chofer.objects.filter(pk=id).first()

    def resolve_chofer_autenticado(self, info):
        user = info.context.user
        return Chofer.objects.filter(usuario=user).first()

    def resolve_check_pin(self, info, pin):
        user = info.context.user
        chofer = Chofer.objects.filter(usuario=user).first()
        return bool(chofer and chofer.pin == pin)

# --- Chofer Mutations ---
class CreateChofer(graphene.Mutation):
    class Arguments:
        user_id         = graphene.Int(required=True)
        nombre          = graphene.String(required=True)
        apellidos       = graphene.String(required=True)
        rfc             = graphene.String(required=True)
        licencia        = graphene.String(required=True)
        certificaciones = graphene.String()
        horario_id      = graphene.Int(required=True)

    chofer = graphene.Field(ChoferType)

    def mutate(self, info, user_id, nombre, apellidos, rfc, licencia, certificaciones, horario_id):
        usuario = User.objects.get(pk=user_id)
        horario = Horario.objects.get(pk=horario_id)
        chofer = Chofer(
            nombre=nombre,
            apellidos=apellidos,
            usuario=usuario,
            rfc=rfc,
            licencia=licencia,
            certificaciones=certificaciones,
            horario=horario,
            pin=None
        )
        chofer.save()
        return CreateChofer(chofer=chofer)

class AssignUserToChofer(graphene.Mutation):
    class Arguments:
        chofer_id = graphene.Int(required=True)
        user_id   = graphene.Int(required=True)

    chofer = graphene.Field(ChoferType)
    ok     = graphene.Boolean()

    def mutate(self, info, chofer_id, user_id):
        try:
            chofer = Chofer.objects.get(pk=chofer_id)
        except Chofer.DoesNotExist:
            raise Exception(f"Chofer con id={chofer_id} no existe")

        try:
            usuario = User.objects.get(pk=user_id)
        except User.DoesNotExist:
            raise Exception(f"Usuario con id={user_id} no existe")

        chofer.usuario = usuario
        chofer.save()
        return AssignUserToChofer(chofer=chofer, ok=True)

class SetChoferPin(graphene.Mutation):
    chofer = graphene.Field(ChoferType)

    class Arguments:
        pin = graphene.String(required=True)

    def mutate(self, info, pin):
        chofer = Chofer.objects.filter(usuario=info.context.user).first()
        if not chofer:
            raise Exception("No estás asociado a ningún chofer")
        if not pin.isdigit() or len(pin) != 4 or es_secuencial(pin):
            raise Exception("PIN inválido")
        chofer.pin = pin
        chofer.save()
        return SetChoferPin(chofer=chofer)

class UpdateChoferPin(graphene.Mutation):
    chofer = graphene.Field(ChoferType)

    class Arguments:
        old_pin = graphene.String(required=True)
        new_pin = graphene.String(required=True)

    def mutate(self, info, old_pin, new_pin):
        chofer = Chofer.objects.filter(usuario=info.context.user).first()
        if not chofer:
            raise Exception("No estás asociado a ningún chofer")
        if chofer.pin != old_pin or not new_pin.isdigit() or len(new_pin) != 4 or es_secuencial(new_pin):
            raise Exception("PIN inválido")
        chofer.pin = new_pin
        chofer.save()
        return UpdateChoferPin(chofer=chofer)

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
        chofer = Chofer.objects.get(pk=id)
        chofer.nombre = nombre
        chofer.apellidos = apellidos
        chofer.rfc = rfc
        chofer.licencia = licencia
        chofer.certificaciones = certificaciones
        chofer.save()
        return ActualizarChofer(chofer=chofer)

class EliminarChofer(graphene.Mutation):
    ok = graphene.Boolean()
    class Arguments:
        id = graphene.Int(required=True)

    def mutate(self, info, id):
        chofer = Chofer.objects.get(pk=id)
        chofer.delete()
        return EliminarChofer(ok=True)

# Registro de todas las mutaciones
class Mutation(graphene.ObjectType):
    # JWT Authentication
    token_auth_driver  = TokenAuthDriver.Field()

    # Chofer operations
    create_chofer        = CreateChofer.Field()
    assign_user_to_chofer = AssignUserToChofer.Field()
    set_chofer_pin       = SetChoferPin.Field()
    update_chofer_pin    = UpdateChoferPin.Field()
    actualizar_chofer    = ActualizarChofer.Field()
    eliminar_chofer      = EliminarChofer.Field()

schema = graphene.Schema(query=Query, mutation=Mutation)

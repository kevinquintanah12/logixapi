import graphene
from graphene_django.types import DjangoObjectType
from .models import Chofer
from horarios.models import Horario
from horarios.schema import HorarioType
from django.contrib.auth.models import User

# Función para verificar si un PIN es secuencial
def es_secuencial(pin):
    ascending = all(int(pin[i]) + 1 == int(pin[i+1]) for i in range(len(pin) - 1))
    descending = all(int(pin[i]) - 1 == int(pin[i+1]) for i in range(len(pin) - 1))
    return ascending or descending

# Tipo GraphQL para el modelo Chofer
class ChoferType(DjangoObjectType):
    class Meta:
        model = Chofer

# Definición de consultas GraphQL
class Query(graphene.ObjectType):
    all_choferes = graphene.List(ChoferType)
    chofer_by_id = graphene.Field(ChoferType, id=graphene.Int())
    chofer_autenticado = graphene.Field(ChoferType)
    # Nuevo query para verificar el PIN
    check_pin = graphene.Boolean(pin=graphene.String(required=True))

    def resolve_all_choferes(self, info, **kwargs):
        user = info.context.user
        if not user.is_authenticated:
            raise Exception("Debes estar autenticado para ver la lista de choferes.")
        return Chofer.objects.all()

    def resolve_chofer_by_id(self, info, id):
        user = info.context.user
        if not user.is_authenticated:
            raise Exception("Debes estar autenticado para ver los detalles de un chofer.")
        try:
            return Chofer.objects.get(pk=id)
        except Chofer.DoesNotExist:
            return None

    def resolve_chofer_autenticado(self, info):
        user = info.context.user
        if not user.is_authenticated:
            raise Exception("Debes estar autenticado para ver tu información.")
        try:
            return Chofer.objects.get(usuario=user)
        except Chofer.DoesNotExist:
            raise Exception("No tienes un chofer asociado a tu cuenta.")

    def resolve_check_pin(self, info, pin):
        user = info.context.user
        if not user.is_authenticated:
            raise Exception("Debes estar autenticado para verificar el PIN.")
        try:
            chofer = Chofer.objects.get(usuario=user)
        except Chofer.DoesNotExist:
            raise Exception("No se encontró un chofer asociado a tu cuenta.")
        # Compara el PIN ingresado con el almacenado en el chofer
        return chofer.pin == pin

# Mutación para crear un Chofer recibiendo el userId como argumento
class CreateChofer(graphene.Mutation):
    class Arguments:
        user_id = graphene.Int(required=True)  # Se añade userId como argumento
        nombre = graphene.String(required=True)
        apellidos = graphene.String(required=True)
        rfc = graphene.String(required=True)
        licencia = graphene.String(required=True)
        certificaciones = graphene.String()
        horario_id = graphene.Int(required=True)

    chofer = graphene.Field(ChoferType)

    def mutate(self, info, user_id, nombre, apellidos, rfc, licencia, certificaciones, horario_id):
        # Buscar el usuario por id
        try:
            usuario = User.objects.get(id=user_id)
        except User.DoesNotExist:
            raise Exception("El usuario especificado no existe.")

        # Verificar que el horario existe
        try:
            horario = Horario.objects.get(id=horario_id)
        except Horario.DoesNotExist:
            raise Exception("El horario especificado no existe.")

        # Crear el chofer asignándole el usuario encontrado
        chofer = Chofer(
            nombre=nombre,
            apellidos=apellidos,
            usuario=usuario,
            rfc=rfc,
            licencia=licencia,
            certificaciones=certificaciones,
            horario=horario,
            pin=None  # Se inicializa sin PIN
        )
        chofer.save()
        return CreateChofer(chofer=chofer)

# Mutación para establecer el PIN del chofer
class SetChoferPin(graphene.Mutation):
    class Arguments:
        pin = graphene.String(required=True)

    chofer = graphene.Field(ChoferType)

    def mutate(self, info, pin):
        user = info.context.user
        if not user.is_authenticated:
            raise Exception("Debes estar autenticado para establecer un PIN.")

        try:
            chofer = Chofer.objects.get(usuario=user)
        except Chofer.DoesNotExist:
            raise Exception("No tienes permiso para establecer un PIN.")

        if not pin.isdigit() or len(pin) != 4:
            raise Exception("El PIN debe contener exactamente 4 dígitos numéricos.")

        if es_secuencial(pin):
            raise Exception("El PIN no puede ser una secuencia numérica.")

        chofer.pin = pin
        chofer.save()
        return SetChoferPin(chofer=chofer)

# Mutación para actualizar el PIN del chofer
class UpdateChoferPin(graphene.Mutation):
    class Arguments:
        pin = graphene.String(required=True)

    chofer = graphene.Field(ChoferType)

    def mutate(self, info, pin):
        user = info.context.user
        if not user.is_authenticated:
            raise Exception("Debes estar autenticado para editar el PIN.")

        try:
            chofer = Chofer.objects.get(usuario=user)
        except Chofer.DoesNotExist:
            raise Exception("No tienes permiso para editar el PIN.")

        if not pin.isdigit() or len(pin) != 4:
            raise Exception("El PIN debe contener exactamente 4 dígitos numéricos.")

        if es_secuencial(pin):
            raise Exception("El PIN no puede ser una secuencia numérica.")

        chofer.pin = pin
        chofer.save()
        return UpdateChoferPin(chofer=chofer)

# Definición de Mutaciones
class Mutation(graphene.ObjectType):
    create_chofer = CreateChofer.Field()
    set_chofer_pin = SetChoferPin.Field()
    update_chofer_pin = UpdateChoferPin.Field()

# Definición del esquema GraphQL
schema = graphene.Schema(query=Query, mutation=Mutation)

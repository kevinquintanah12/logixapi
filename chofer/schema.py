import graphene
from graphene_django.types import DjangoObjectType
from .models import Chofer
from horarios.models import Horario
from horarios.schema import HorarioType
from django.contrib.auth.models import User

def es_secuencial(pin):
    # Verifica si los dígitos están en secuencia ascendente o descendente
    ascending = all(int(pin[i]) + 1 == int(pin[i+1]) for i in range(len(pin) - 1))
    descending = all(int(pin[i]) - 1 == int(pin[i+1]) for i in range(len(pin) - 1))
    return ascending or descending

class ChoferType(DjangoObjectType):
    class Meta:
        model = Chofer

class Query(graphene.ObjectType):
    all_choferes = graphene.List(ChoferType)
    chofer_by_id = graphene.Field(ChoferType, id=graphene.Int())

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

# Mutación para crear un Chofer (sin PIN)
class CreateChofer(graphene.Mutation):
    class Arguments:
        nombre = graphene.String(required=True)
        apellidos = graphene.String(required=True)
        rfc = graphene.String(required=True)
        licencia = graphene.String(required=True)
        certificaciones = graphene.String()
        horario_id = graphene.Int(required=True)

    chofer = graphene.Field(ChoferType)

    def mutate(self, info, nombre, apellidos, rfc, licencia, certificaciones, horario_id):
        user = info.context.user
        if not user.is_authenticated:
            raise Exception("Debes estar autenticado para crear un chofer.")

        horario = Horario.objects.get(id=horario_id)
        chofer = Chofer(
            nombre=nombre,
            apellidos=apellidos,
            usuario=user,  # Se asigna directamente el usuario autenticado
            rfc=rfc,
            licencia=licencia,
            certificaciones=certificaciones,
            horario=horario,
            pin=None  # Inicialmente sin PIN
        )
        chofer.save()
        return CreateChofer(chofer=chofer)

# Mutación para que el chofer cree su PIN después
class SetChoferPin(graphene.Mutation):
    class Arguments:
        pin = graphene.String(required=True)

    chofer = graphene.Field(ChoferType)

    def mutate(self, info, pin):
        user = info.context.user  # Obtener usuario autenticado
        if not user.is_authenticated:
            raise Exception("Debes estar autenticado para establecer un PIN.")

        try:
            chofer = Chofer.objects.get(usuario=user)
        except Chofer.DoesNotExist:
            raise Exception("No tienes permiso para establecer un PIN.")

        # Validación: El PIN debe ser un número de 4 dígitos
        if not pin.isdigit() or len(pin) != 4:
            raise Exception("El PIN debe contener exactamente 4 dígitos numéricos.")

        # Validación: El PIN no debe ser secuencial
        if es_secuencial(pin):
            raise Exception("El PIN no puede ser una secuencia numérica.")

        chofer.pin = pin
        chofer.save()
        return SetChoferPin(chofer=chofer)

# Mutación para editar (actualizar) el PIN del chofer existente
class UpdateChoferPin(graphene.Mutation):
    class Arguments:
        pin = graphene.String(required=True)

    chofer = graphene.Field(ChoferType)

    def mutate(self, info, pin):
        user = info.context.user  # Obtener usuario autenticado
        if not user.is_authenticated:
            raise Exception("Debes estar autenticado para editar el PIN.")

        try:
            chofer = Chofer.objects.get(usuario=user)
        except Chofer.DoesNotExist:
            raise Exception("No tienes permiso para editar el PIN.")

        # Validación: El PIN debe ser un número de 4 dígitos
        if not pin.isdigit() or len(pin) != 4:
            raise Exception("El PIN debe contener exactamente 4 dígitos numéricos.")

        # Validación: El PIN no debe ser secuencial
        if es_secuencial(pin):
            raise Exception("El PIN no puede ser una secuencia numérica.")

        chofer.pin = pin
        chofer.save()
        return UpdateChoferPin(chofer=chofer)

class Mutation(graphene.ObjectType):
    create_chofer = CreateChofer.Field()
    set_chofer_pin = SetChoferPin.Field()
    update_chofer_pin = UpdateChoferPin.Field()

schema = graphene.Schema(query=Query, mutation=Mutation)

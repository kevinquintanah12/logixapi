import graphene
from graphene_django.types import DjangoObjectType
from .models import Horario

class HorarioType(DjangoObjectType):
    class Meta:
        model = Horario

class Query(graphene.ObjectType):
    all_horarios = graphene.List(HorarioType)
    horario_by_id = graphene.Field(HorarioType, id=graphene.Int())

    def resolve_all_horarios(self, info, **kwargs):
        return Horario.objects.all()

    def resolve_horario_by_id(self, info, id):
        try:
            return Horario.objects.get(pk=id)
        except Horario.DoesNotExist:
            return None

class CreateHorario(graphene.Mutation):
    class Arguments:
        nombre = graphene.String(required=True)
        hora_inicio = graphene.Time(required=True)
        hora_fin = graphene.Time(required=True)

    horario = graphene.Field(HorarioType)

    def mutate(self, info, nombre, hora_inicio, hora_fin):
        horario = Horario(nombre=nombre, hora_inicio=hora_inicio, hora_fin=hora_fin)
        horario.save()
        return CreateHorario(horario=horario)

class Mutation(graphene.ObjectType):
    create_horario = CreateHorario.Field()  # Verifica que está registrado aquí

schema = graphene.Schema(query=Query, mutation=Mutation)

import graphene
from graphene_django import DjangoObjectType
from .models import CentroDistribucion
from Ubicacion.models import Ubicacion  # Importa el modelo Ubicacion
from Ubicacion.schema import UbicacionType

class CentroDistribucionType(DjangoObjectType):
    class Meta:
        model = CentroDistribucion

# Consultas
class Query(graphene.ObjectType):
    centros_distribucion = graphene.List(CentroDistribucionType)
    centro_distribucion = graphene.Field(CentroDistribucionType, id=graphene.Int(required=True))

    def resolve_centros_distribucion(self, info):
        return CentroDistribucion.objects.all()

    def resolve_centro_distribucion(self, info, id):
        return CentroDistribucion.objects.get(id=id)

# Mutaciones
class DarAltaCentroDistribucion(graphene.Mutation):
    class Arguments:
        ubicacion_id = graphene.Int(required=True)

    centro_distribucion = graphene.Field(CentroDistribucionType)

    def mutate(self, info, ubicacion_id):
        try:
            ubicacion = Ubicacion.objects.get(id=ubicacion_id)
            centro_distribucion = CentroDistribucion.objects.create(
                ubicacion=ubicacion
            )
            return DarAltaCentroDistribucion(centro_distribucion=centro_distribucion)
        except Ubicacion.DoesNotExist:
            raise Exception("Ubicación no encontrada")

class Mutation(graphene.ObjectType):
    dar_alta_centro_distribucion = DarAltaCentroDistribucion.Field()

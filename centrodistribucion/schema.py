import graphene
from graphene_django import DjangoObjectType
from .models import CentroDistribucion
from Ubicacion.models import Ubicacion
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
class CrearCentroDistribucion(graphene.Mutation):
    class Arguments:
        ubicacion_id = graphene.Int(required=True)

    centro_distribucion = graphene.Field(CentroDistribucionType)

    def mutate(self, info, ubicacion_id):
        try:
            ubicacion = Ubicacion.objects.get(id=ubicacion_id)
            centro = CentroDistribucion.objects.create(ubicacion=ubicacion)
            return CrearCentroDistribucion(centro_distribucion=centro)
        except Ubicacion.DoesNotExist:
            raise Exception("Ubicación no encontrada")

class ActualizarCentroDistribucion(graphene.Mutation):
    class Arguments:
        id = graphene.Int(required=True)
        ubicacion_id = graphene.Int(required=True)

    centro_distribucion = graphene.Field(CentroDistribucionType)

    def mutate(self, info, id, ubicacion_id):
        try:
            centro = CentroDistribucion.objects.get(id=id)
            ubicacion = Ubicacion.objects.get(id=ubicacion_id)
            centro.ubicacion = ubicacion
            centro.save()
            return ActualizarCentroDistribucion(centro_distribucion=centro)
        except CentroDistribucion.DoesNotExist:
            raise Exception("Centro de distribución no encontrado")
        except Ubicacion.DoesNotExist:
            raise Exception("Ubicación no encontrada")

class EliminarCentroDistribucion(graphene.Mutation):
    class Arguments:
        id = graphene.Int(required=True)

    ok = graphene.Boolean()

    def mutate(self, info, id):
        try:
            centro = CentroDistribucion.objects.get(id=id)
            centro.delete()
            return EliminarCentroDistribucion(ok=True)
        except CentroDistribucion.DoesNotExist:
            raise Exception("Centro de distribución no encontrado")

# Mutaciones raíz
class Mutation(graphene.ObjectType):
    crear_centro_distribucion = CrearCentroDistribucion.Field()
    actualizar_centro_distribucion = ActualizarCentroDistribucion.Field()
    eliminar_centro_distribucion = EliminarCentroDistribucion.Field()

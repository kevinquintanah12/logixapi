from decimal import Decimal
import graphene
from graphene_django import DjangoObjectType
from .models import Ubicacion
from graphql_jwt.decorators import login_required  # Para requerir autenticación

class UbicacionType(DjangoObjectType):
    class Meta:
        model = Ubicacion

# Consultas
class Query(graphene.ObjectType):
    ubicaciones = graphene.List(UbicacionType)

    @login_required
    def resolve_ubicaciones(self, info):
        return Ubicacion.objects.all()

# Mutaciones
class CrearUbicacion(graphene.Mutation):
    class Arguments:
        ciudad = graphene.String(required=True)
        estado = graphene.String(required=True)
        latitud = graphene.Float(required=True)
        longitud = graphene.Float(required=True)

    ubicacion = graphene.Field(UbicacionType)

    @login_required
    def mutate(self, info, ciudad, estado, latitud, longitud):
        latitud = Decimal(str(latitud))  # Convertir a Decimal
        longitud = Decimal(str(longitud))  # Convertir a Decimal

        ubicacion = Ubicacion.objects.create(
            ciudad=ciudad,
            estado=estado,
            latitud=latitud,
            longitud=longitud
        )
        return CrearUbicacion(ubicacion=ubicacion)

class Mutation(graphene.ObjectType):
    crear_ubicacion = CrearUbicacion.Field()

# Definir el esquema GraphQL
schema = graphene.Schema(query=Query, mutation=Mutation)

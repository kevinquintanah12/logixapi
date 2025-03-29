from decimal import Decimal
import graphene
import requests
from graphene_django import DjangoObjectType
from .models import Ubicacion
from graphql_jwt.decorators import login_required

# Token de acceso de Mapbox
MAPBOX_ACCESS_TOKEN = "pk.eyJ1IjoiZGF5a2V2MTIiLCJhIjoiY204MTd5NzR3MGdxYTJqcGlsa29odnQ5YiJ9.tbAEt453VxfJoDatpU72YQ"

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

    ubicacion = graphene.Field(UbicacionType)

    @login_required
    def mutate(self, info, ciudad, estado):
        # Obtener coordenadas usando la API de Mapbox
        query = f"{ciudad}, {estado}"
        url = f"https://api.mapbox.com/geocoding/v5/mapbox.places/{query}.json?access_token={MAPBOX_ACCESS_TOKEN}"

        response = requests.get(url)
        if response.status_code != 200:
            raise Exception("Error al conectarse con la API de Mapbox.")

        data = response.json()
        if not data.get("features"):
            raise Exception("No se encontraron coordenadas para la ubicación proporcionada.")

        # Extraer coordenadas (Mapbox devuelve [longitud, latitud])
        longitud, latitud = data["features"][0]["geometry"]["coordinates"]

        # Convertir a Decimal antes de guardar en la base de datos
        latitud = Decimal(str(latitud))
        longitud = Decimal(str(longitud))

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

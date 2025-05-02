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

class Query(graphene.ObjectType):
    # Obtener todas las ubicaciones detalladas
    ubicaciones = graphene.List(UbicacionType)
    # Lista para ComboBox ("id: ciudad, estado")
    ubicaciones_list = graphene.List(graphene.String)

    @login_required
    def resolve_ubicaciones(self, info):
        return Ubicacion.objects.all()

    @login_required
    def resolve_ubicaciones_list(self, info):
        return [
            f"{u.id}: {u.ciudad}, {u.estado}"
            for u in Ubicacion.objects.all()
        ]

# Mutaciones
class CrearUbicacion(graphene.Mutation):
    class Arguments:
        ciudad = graphene.String(required=True)
        estado = graphene.String(required=True)

    ubicacion = graphene.Field(UbicacionType)

    @login_required
    def mutate(self, info, ciudad, estado):
        # Obtener coordenadas de Mapbox
        query = f"{ciudad}, {estado}"
        url = (
            f"https://api.mapbox.com/geocoding/v5/mapbox.places/"
            f"{query}.json?access_token={MAPBOX_ACCESS_TOKEN}"
        )
        resp = requests.get(url)
        if resp.status_code != 200:
            raise Exception("Error al conectarse con la API de Mapbox.")
        data = resp.json()
        if not data.get("features"):
            raise Exception("No se encontraron coordenadas para la ubicación dada.")

        lon, lat = data["features"][0]["geometry"]["coordinates"]
        ubicacion = Ubicacion.objects.create(
            ciudad=ciudad,
            estado=estado,
            latitud=Decimal(str(lat)),
            longitud=Decimal(str(lon))
        )
        return CrearUbicacion(ubicacion=ubicacion)

class ActualizarUbicacion(graphene.Mutation):
    class Arguments:
        id = graphene.ID(required=True)
        ciudad = graphene.String()
        estado = graphene.String()

    ubicacion = graphene.Field(UbicacionType)

    @login_required
    def mutate(self, info, id, ciudad=None, estado=None):
        try:
            ubicacion = Ubicacion.objects.get(pk=id)
        except Ubicacion.DoesNotExist:
            raise Exception("Ubicación no encontrada.")

        # Actualizar campos
        if ciudad:
            ubicacion.ciudad = ciudad
        if estado:
            ubicacion.estado = estado

        # Si cambió ubicación, actualizar coordenadas
        if ciudad or estado:
            query = f"{ubicacion.ciudad}, {ubicacion.estado}"
            url = (
                f"https://api.mapbox.com/geocoding/v5/mapbox.places/"
                f"{query}.json?access_token={MAPBOX_ACCESS_TOKEN}"
            )
            resp = requests.get(url)
            if resp.status_code != 200:
                raise Exception("Error al actualizar coordenadas en Mapbox.")
            data = resp.json()
            if not data.get("features"):
                raise Exception("No se encontraron nuevas coordenadas.")
            lon, lat = data["features"][0]["geometry"]["coordinates"]
            ubicacion.latitud = Decimal(str(lat))
            ubicacion.longitud = Decimal(str(lon))

        ubicacion.save()
        return ActualizarUbicacion(ubicacion=ubicacion)

class EliminarUbicacion(graphene.Mutation):
    class Arguments:
        id = graphene.ID(required=True)

    ok = graphene.Boolean()

    @login_required
    def mutate(self, info, id):
        try:
            ubicacion = Ubicacion.objects.get(pk=id)
        except Ubicacion.DoesNotExist:
            raise Exception("Ubicación no encontrada.")
        ubicacion.delete()
        return EliminarUbicacion(ok=True)

class Mutation(graphene.ObjectType):
    crear_ubicacion = CrearUbicacion.Field()
    actualizar_ubicacion = ActualizarUbicacion.Field()
    eliminar_ubicacion = EliminarUbicacion.Field()

schema = graphene.Schema(query=Query, mutation=Mutation)

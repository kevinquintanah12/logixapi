import graphene
from graphene_django import DjangoObjectType
from .models import SensorRuta
from rutas.models import Ruta  # para validación

class SensorRutaType(DjangoObjectType):
    class Meta:
        model = SensorRuta

class CrearSensorRuta(graphene.Mutation):
    class Arguments:
        ruta_id = graphene.ID(required=True)
        latitud = graphene.Float(required=True)
        longitud = graphene.Float(required=True)
        temperatura = graphene.Float(required=True)
        humedad = graphene.Float(required=True)

    sensor = graphene.Field(SensorRutaType)

    def mutate(self, info, ruta_id, latitud, longitud, temperatura, humedad):
        ruta = Ruta.objects.get(id=ruta_id)
        sensor = SensorRuta.objects.create(
            ruta=ruta,
            latitud=latitud,
            longitud=longitud,
            temperatura=temperatura,
            humedad=humedad
        )
        return CrearSensorRuta(sensor=sensor)

class Query(graphene.ObjectType):
    sensores_por_ruta = graphene.List(SensorRutaType, ruta_id=graphene.ID(required=True))

    def resolve_sensores_por_ruta(self, info, ruta_id):
        return SensorRuta.objects.filter(ruta_id=ruta_id).order_by('-timestamp')

class Mutation(graphene.ObjectType):
    crear_sensor_ruta = CrearSensorRuta.Field()

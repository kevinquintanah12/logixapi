import graphene
from graphene_django import DjangoObjectType
from graphql_jwt.decorators import login_required
from decimal import Decimal
from .models import CalcularEnvio
from tipoproductos.models import TipoProducto, Temperatura, Humedad
import requests
import math

from Ubicacion.models import Ubicacion  # Ajusta el import según tu proyecto

MAPBOX_ACCESS_TOKEN = "pk.eyJ1IjoiZGF5a2V2MTIiLCJhIjoiY204MTd5NzR3MGdxYTJqcGlsa29odnQ5YiJ9.tbAEt453VxfJoDatpU72YQ"

class CalcularEnvioType(DjangoObjectType):
    descripcion = graphene.String()
    totalTarifa = graphene.Decimal()
    tarifaKm = graphene.Decimal()
    tarifaPeso = graphene.Decimal()
    distanciaKm = graphene.Decimal()

    class Meta:
        model = CalcularEnvio
        fields = "__all__"

    def resolve_totalTarifa(self, info):
        return self.total_tarifa

    def resolve_tarifaKm(self, info):
        return self.tarifa_km

    def resolve_tarifaPeso(self, info):
        return self.tarifa_peso

    def resolve_distanciaKm(self, info):
        return self.distancia_km

class Query(graphene.ObjectType):
    calcular_envio = graphene.Field(CalcularEnvioType, id=graphene.Int(required=True))
    ultimo_calculo = graphene.Field(CalcularEnvioType)  # Nuevo campo para obtener el último cálculo

    def resolve_calcular_envio(self, info, id):
        return CalcularEnvio.objects.get(id=id)

    def resolve_ultimo_calculo(self, info):
        # Obtener el último cálculo de envío (por el ID más alto)
        return CalcularEnvio.objects.latest('id')

class CrearCalcularEnvio(graphene.Mutation):
    class Arguments:
        tipo_producto_id = graphene.Int(required=True)
        origen_cd_id = graphene.Int(required=True)
        destino_id = graphene.Int(required=True)
        peso_unitario = graphene.Float(required=True)
        numero_piezas = graphene.Int(required=True)
        dimensiones_largo = graphene.Float(required=True)
        dimensiones_ancho = graphene.Float(required=True)
        dimensiones_alto = graphene.Float(required=True)
        descripcion = graphene.String(required=True)
        envio_express = graphene.Boolean(required=True)  # Nuevo argumento

    calcular_envio = graphene.Field(CalcularEnvioType)

    @login_required
    def mutate(self, info, tipo_producto_id, origen_cd_id, destino_id, peso_unitario,
               numero_piezas, dimensiones_largo, dimensiones_ancho, dimensiones_alto,
               descripcion, envio_express):

        tipo_producto = TipoProducto.objects.get(id=tipo_producto_id)
        tarifa_base = Decimal(tipo_producto.precio_base)

        temperatura = Temperatura.objects.filter(tipo_producto_id=tipo_producto_id).first()
        tarifa_extra_temperatura = Decimal(temperatura.tarifa_extra) if temperatura else Decimal(0)

        humedad = Humedad.objects.filter(tipo_producto_id=tipo_producto_id).first()
        tarifa_extra_humedad = Decimal(humedad.tarifa_extra) if humedad else Decimal(0)

        origen = Ubicacion.objects.get(id=origen_cd_id)
        destino = Ubicacion.objects.get(id=destino_id)
        origen_coords = (origen.longitud, origen.latitud)
        destino_coords = (destino.longitud, destino.latitud)

        calcular_envio = CalcularEnvio.objects.create(
            tipo_producto_id=tipo_producto_id,
            origen_cd_id=origen_cd_id,
            destino_id=destino_id,
            peso_unitario=Decimal(peso_unitario),
            numero_piezas=numero_piezas,
            dimensiones_largo=Decimal(dimensiones_largo),
            dimensiones_ancho=Decimal(dimensiones_ancho),
            dimensiones_alto=Decimal(dimensiones_alto),
            tarifa_base=tarifa_base,
            tarifa_extra_temperatura=tarifa_extra_temperatura,
            tarifa_extra_humedad=tarifa_extra_humedad,
            trasladoiva=Decimal(0),
            ieps=Decimal(0),
            descripcion=descripcion
        )

        url = (
            f"https://api.mapbox.com/directions/v5/mapbox/driving/"
            f"{origen_coords[0]},{origen_coords[1]};{destino_coords[0]},{destino_coords[1]}"
        )
        params = {
            'access_token': MAPBOX_ACCESS_TOKEN,
            'geometries': 'geojson'
        }
        response = requests.get(url, params=params)
        data = response.json()
        if not data.get('routes'):
            raise Exception("No se pudo obtener la ruta desde Mapbox.")
        distance_meters = data['routes'][0]['distance']
        distance_km = distance_meters / 1000

        tramos = math.ceil(distance_km / 30)
        tarifa_por_km = Decimal(tramos * 4)

        tarifa_por_peso = Decimal(peso_unitario * numero_piezas) * Decimal(5)

        subtotal = tarifa_base + tarifa_extra_temperatura + tarifa_extra_humedad + tarifa_por_km + tarifa_por_peso

        iva_calculado = subtotal * Decimal('0.10')
        ieps_calculado = subtotal * Decimal('0.10')

        total_final = subtotal + iva_calculado + ieps_calculado

        if envio_express:
            total_final += Decimal(900)  # Se suman 900 pesos si es express

        calcular_envio.tarifa_km = tarifa_por_km
        calcular_envio.tarifa_peso = tarifa_por_peso
        calcular_envio.distancia_km = Decimal(distance_km)
        calcular_envio.trasladoiva = iva_calculado
        calcular_envio.ieps = ieps_calculado
        calcular_envio.total_tarifa = total_final
        calcular_envio.save()

        return CrearCalcularEnvio(calcular_envio=calcular_envio)

class Mutation(graphene.ObjectType):
    crear_calcular_envio = CrearCalcularEnvio.Field()

schema = graphene.Schema(query=Query, mutation=Mutation)

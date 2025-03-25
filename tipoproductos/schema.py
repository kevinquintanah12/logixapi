import graphene
from graphene_django import DjangoObjectType
from graphql_jwt.decorators import login_required
from .models import TipoProducto, Temperatura, Humedad
from decimal import Decimal

# Tipos de GraphQL
class TipoProductoType(DjangoObjectType):
    class Meta:
        model = TipoProducto

class TemperaturaType(DjangoObjectType):
    class Meta:
        model = Temperatura

class HumedadType(DjangoObjectType):
    class Meta:
        model = Humedad

# Consultas
class Query(graphene.ObjectType):
    tipo_productos = graphene.List(TipoProductoType)
    temperatura = graphene.Field(TemperaturaType, tipo_producto_id=graphene.Int(required=True))
    humedad = graphene.Field(HumedadType, tipo_producto_id=graphene.Int(required=True))

    @login_required
    def resolve_tipo_productos(self, info):
        return TipoProducto.objects.all()

    @login_required
    def resolve_temperatura(self, info, tipo_producto_id):
        return Temperatura.objects.filter(tipo_producto_id=tipo_producto_id).first()

    @login_required
    def resolve_humedad(self, info, tipo_producto_id):
        return Humedad.objects.filter(tipo_producto_id=tipo_producto_id).first()

# Mutaciones
class CrearTipoProducto(graphene.Mutation):
    class Arguments:
        nombre = graphene.String(required=True)
        descripcion = graphene.String(required=True)
        precio_base = graphene.Float(required=True)

    tipo_producto = graphene.Field(TipoProductoType)

    @login_required
    def mutate(self, info, nombre, descripcion, precio_base):
        precio_base_decimal = Decimal(precio_base)

        tipo_producto = TipoProducto.objects.create(
            nombre=nombre,
            descripcion=descripcion,
            precio_base=precio_base_decimal

        )
        return CrearTipoProducto(tipo_producto=tipo_producto)

class CrearTemperatura(graphene.Mutation):
    class Arguments:
        tipo_producto_id = graphene.Int(required=True)
        rango_minimo = graphene.Int(required=True)
        rango_maximo = graphene.Int(required=True)
        tarifa_extra = graphene.Float(required=False, default_value=0)

    temperatura = graphene.Field(TemperaturaType)

    @login_required
    def mutate(self, info, tipo_producto_id, rango_minimo, rango_maximo, tarifa_extra):
        tipo_producto = TipoProducto.objects.get(id=tipo_producto_id)
        temperatura = Temperatura.objects.create(
            tipo_producto=tipo_producto,
            rango_minimo=rango_minimo,
            rango_maximo=rango_maximo,
            tarifa_extra=Decimal(tarifa_extra)  # <- Convertimos a Decimal antes de guardar
        )
        return CrearTemperatura(temperatura=temperatura)

class CrearHumedad(graphene.Mutation):
    class Arguments:
        tipo_producto_id = graphene.Int(required=True)
        rango_minimo = graphene.Int(required=True)
        rango_maximo = graphene.Int(required=True)
        tarifa_extra = graphene.Float(required=False, default_value=0)

    humedad = graphene.Field(HumedadType)

    @login_required
    def mutate(self, info, tipo_producto_id, rango_minimo, rango_maximo, tarifa_extra):
        tipo_producto = TipoProducto.objects.get(id=tipo_producto_id)
        humedad = Humedad.objects.create(
            tipo_producto=tipo_producto,
            rango_minimo=rango_minimo,
            rango_maximo=rango_maximo,
            tarifa_extra=Decimal(tarifa_extra)  # <- Convertimos a Decimal antes de guardar
        )
        return CrearHumedad(humedad=humedad)

# Registrar mutaciones
class Mutation(graphene.ObjectType):
    crear_tipo_producto = CrearTipoProducto.Field()
    crear_temperatura = CrearTemperatura.Field()
    crear_humedad = CrearHumedad.Field()

# Definir el esquema GraphQL
schema = graphene.Schema(query=Query, mutation=Mutation)

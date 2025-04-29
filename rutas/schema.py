import asyncio
async def _patched_wait(aws, *args, **kwargs):
    loop    = asyncio.get_event_loop()
    wrapped = [
        loop.create_task(a) if asyncio.iscoroutine(a) else a
        for a in aws
    ]
    return await _original_wait(wrapped, *args, **kwargs)
asyncio.wait = _patched_wait

import graphene
from graphene_django.types import DjangoObjectType
from channels_graphql_ws import Subscription
from asgiref.sync import async_to_sync
from graphql_jwt.decorators import login_required

# Modelos
from .models         import Ruta
from chofer.models   import Chofer
from camiones.models import Camion
from entrega.models  import Entrega
from paquete.models  import Paquete
from producto.models import Producto

# Tipos de Paquete y Producto (si los tienes en otro módulo, importa aquí)
class ProductoType(DjangoObjectType):
    class Meta:
        model  = Producto
        fields = '__all__'

class PaqueteType(DjangoObjectType):
    producto = graphene.Field(ProductoType)

    class Meta:
        model  = Paquete
        fields = ('id', 'numero_guia', 'codigo_barras', 'fecha_registro', 'producto')

    def resolve_producto(self, info):
        return self.producto

# Tipo de Entrega para permitir nested en Ruta
class EntregaType(DjangoObjectType):
    paquete = graphene.Field(PaqueteType)

    class Meta:
        model  = Entrega
        fields = ('id', 'fechaEntrega', 'estado', 'paquete')

    def resolve_paquete(self, info):
        return self.paquete

# Tipo de Ruta con entregas anidadas
class RutaType(DjangoObjectType):
    entregas = graphene.List(EntregaType)

    class Meta:
        model  = Ruta
        fields = '__all__'

    def resolve_entregas(self, info):
        return self.entregas.all()

# Subscriptions
class RutaPorEstadoSubscription(Subscription):
    ruta   = graphene.Field(RutaType)
    estado = graphene.String()

    class Arguments:
        estado = graphene.String(required=True)

    def subscribe(self, info, estado):
        return [estado]

    @classmethod
    def publish(cls, payload, info, estado):
        return cls(ruta=payload['ruta'], estado=estado)

    @classmethod
    def broadcast_ruta(cls, ruta_obj):
        async_to_sync(cls.broadcast)(
            group   = ruta_obj.estado,
            payload = { 'ruta': ruta_obj }
        )

class TodasRutasSubscription(Subscription):
    ruta = graphene.Field(RutaType)

    def subscribe(self, info):
        return ['all']

    @classmethod
    def publish(cls, payload, info):
        return cls(ruta=payload['ruta'])

    @classmethod
    def broadcast_ruta(cls, ruta_obj):
        async_to_sync(cls.broadcast)(
            group   = 'all',
            payload = { 'ruta': ruta_obj }
        )

# Mutations de Ruta
def handle_fcm_notification(user, title, body):
    try:
        device = FCMDevice.objects.get(user=user)
        enviar_notificacion_fcm_v1(token=device.token, title=title, body=body)
    except Exception:
        pass

class CrearRuta(graphene.Mutation):
    class Arguments:
        distancia     = graphene.Float(required=True)
        prioridad     = graphene.Int(required=True)
        conductor_id  = graphene.Int(required=True)
        vehiculo_id   = graphene.Int(required=True)
        fecha_inicio  = graphene.DateTime(required=True)
        fecha_fin     = graphene.DateTime(required=True)
        estado        = graphene.String(required=False, default_value='por hacer')
        entrega_id    = graphene.Int(required=True)

    ruta = graphene.Field(RutaType)

    def mutate(self, info, distancia, prioridad, conductor_id, vehiculo_id, fecha_inicio, fecha_fin, estado, entrega_id):
        vehiculo  = Camion.objects.get(id=vehiculo_id)
        conductor = Chofer.objects.get(id=conductor_id)
        entrega   = Entrega.objects.get(id=entrega_id)

        ruta = Ruta.objects.create(
            distancia    = distancia,
            prioridad    = prioridad,
            conductor    = conductor,
            vehiculo     = vehiculo,
            fecha_inicio = fecha_inicio,
            fecha_fin    = fecha_fin,
            estado       = estado,
        )
        ruta.entregas.add(entrega)

        handle_fcm_notification(conductor.usuario, 'Nueva Ruta Asignada', 'Tienes una ruta nueva.')
        RutaPorEstadoSubscription.broadcast_ruta(ruta)
        TodasRutasSubscription.broadcast_ruta(ruta)

        return CrearRuta(ruta=ruta)

class CambiarEstadoRuta(graphene.Mutation):
    class Arguments:
        ruta_id      = graphene.Int(required=True)
        nuevo_estado = graphene.String(required=True)

    ruta = graphene.Field(RutaType)

    def mutate(self, info, ruta_id, nuevo_estado):
        ruta = Ruta.objects.get(id=ruta_id)
        ruta.estado = nuevo_estado
        ruta.save()

        handle_fcm_notification(ruta.conductor.usuario, 'Ruta Actualizada', f"Ruta {ruta_id} cambió a '{nuevo_estado}'.")
        RutaPorEstadoSubscription.broadcast_ruta(ruta)
        TodasRutasSubscription.broadcast_ruta(ruta)

        return CambiarEstadoRuta(ruta=ruta)

# Queries
types_list = [ProductoType, PaqueteType, EntregaType, RutaType]

class Query(paquete_schema.Query, graphene.ObjectType, RutaType):
    pass

# Mutations root
class Mutation(paquete_schema.Mutation, graphene.ObjectType):
    crear_ruta          = CrearRuta.Field()
    cambiar_estado_ruta = CambiarEstadoRuta.Field()

# Subscription root
class SubscriptionRoot(graphene.ObjectType):
    ruta_por_estado = RutaPorEstadoSubscription.Field()
    todas_rutas     = TodasRutasSubscription.Field()

# Schema final
schema = graphene.Schema(
    query        = Query,
    mutation     = Mutation,
    subscription = SubscriptionRoot,
    types        = types_list
)

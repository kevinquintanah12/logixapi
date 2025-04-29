# schema.py (esquema raíz unificado)

# ──────────────────────────────────────────────────────────────────────────────
# 0) Parche asyncio.wait para channels_graphql_ws
# ──────────────────────────────────────────────────────────────────────────────
import asyncio
_original_wait = asyncio.wait

async def _patched_wait(aws, *args, **kwargs):
    loop = asyncio.get_event_loop()
    wrapped = [
        loop.create_task(a) if asyncio.iscoroutine(a) else a
        for a in aws
    ]
    return await _original_wait(wrapped, *args, **kwargs)

asyncio.wait = _patched_wait


# ──────────────────────────────────────────────────────────────────────────────
# 1) Imports básicos de Graphene, Django y tus modelos
# ──────────────────────────────────────────────────────────────────────────────
import graphene
from graphene_django.types import DjangoObjectType
from channels_graphql_ws import Subscription
from asgiref.sync import async_to_sync
from graphql_jwt.decorators import login_required

from .models         import Ruta
from chofer.models   import Chofer
from camiones.models import Camion
from entrega.models  import Entrega

from paquete.models  import Paquete
from fcm.firebase_config import enviar_notificacion_fcm_v1
from fcm.models          import FCMDevice


# ──────────────────────────────────────────────────────────────────────────────
# 2) Importa tus esquemas parciales
#    - producto.schema define ProductoType
#    - paquete.schema define PaqueteType y sus Query/Mutation
#    - entrega.schema define EntregaType y su Query (si la tienes)
# ──────────────────────────────────────────────────────────────────────────────
import producto.schema      as producto_schema
import paquete.schema       as paquete_schema
import entrega.schema       as entrega_schema


# ──────────────────────────────────────────────────────────────────────────────
# 3) Tipo GraphQL para Ruta (añade entregas usando EntregaType importado)
# ──────────────────────────────────────────────────────────────────────────────
class RutaType(DjangoObjectType):
    entregas = graphene.List(entrega_schema.EntregaType)

    class Meta:
        model  = Ruta
        # Lista explícita para exponer entregas
        fields = (
            "id",
            "distancia",
            "prioridad",
            "conductor",
            "vehiculo",
            "fecha_inicio",
            "fecha_fin",
            "estado",
            "entregas",
        )

    def resolve_entregas(self, info):
        return self.entregas.all()


# ──────────────────────────────────────────────────────────────────────────────
# 4) Subscriptions de Ruta
# ──────────────────────────────────────────────────────────────────────────────
class RutaPorEstadoSubscription(Subscription):
    ruta   = graphene.Field(RutaType)
    estado = graphene.String()

    class Arguments:
        estado = graphene.String(required=True)

    def subscribe(self, info, estado):
        return [estado]

    @classmethod
    def publish(cls, payload, info, estado):
        return cls(ruta=payload["ruta"], estado=estado)

    @classmethod
    def broadcast_ruta(cls, ruta_obj):
        async_to_sync(cls.broadcast)(
            group   = ruta_obj.estado,
            payload = {"ruta": ruta_obj}
        )

class TodasRutasSubscription(Subscription):
    ruta = graphene.Field(RutaType)

    def subscribe(self, info):
        return ["all"]

    @classmethod
    def publish(cls, payload, info):
        return cls(ruta=payload["ruta"])

    @classmethod
    def broadcast_ruta(cls, ruta_obj):
        async_to_sync(cls.broadcast)(
            group   = "all",
            payload = {"ruta": ruta_obj}
        )


# ──────────────────────────────────────────────────────────────────────────────
# 5) Mutations de Ruta
# ──────────────────────────────────────────────────────────────────────────────
class CrearRuta(graphene.Mutation):
    class Arguments:
        distancia     = graphene.Float(required=True)
        prioridad     = graphene.Int(required=True)
        conductor_id  = graphene.Int(required=True)
        vehiculo_id   = graphene.Int(required=True)
        fecha_inicio  = graphene.DateTime(required=True)
        fecha_fin     = graphene.DateTime(required=True)
        estado        = graphene.String(required=False, default_value="por hacer")
        entrega_id    = graphene.Int(required=True)

    ruta = graphene.Field(RutaType)

    def mutate(self, info, distancia, prioridad, conductor_id, vehiculo_id,
               fecha_inicio, fecha_fin, estado, entrega_id):
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

        # Notificación FCM
        try:
            device = FCMDevice.objects.get(user=conductor.usuario)
            enviar_notificacion_fcm_v1(
                token = device.token,
                title = "Nueva Ruta Asignada",
                body  = "Tienes una ruta nueva."
            )
        except FCMDevice.DoesNotExist:
            print("Chofer sin token FCM.")

        # Emitimos a suscripciones
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

        # Notificación FCM
        try:
            device = FCMDevice.objects.get(user=ruta.conductor.usuario)
            enviar_notificacion_fcm_v1(
                token = device.token,
                title = "Ruta Actualizada",
                body  = f"Ruta {ruta_id} cambió a '{nuevo_estado}'."
            )
        except FCMDevice.DoesNotExist:
            print("Chofer sin token FCM.")

        # Emitimos a suscripciones
        RutaPorEstadoSubscription.broadcast_ruta(ruta)
        TodasRutasSubscription.broadcast_ruta(ruta)

        return CambiarEstadoRuta(ruta=ruta)


# ──────────────────────────────────────────────────────────────────────────────
# 6) Queries de Ruta
# ──────────────────────────────────────────────────────────────────────────────
class RutaQuery(graphene.ObjectType):
    ruta                       = graphene.Field(RutaType, id=graphene.Int(required=True))
    mis_rutas                  = graphene.List(RutaType)
    mis_rutas_por_estado       = graphene.List(RutaType, estado=graphene.String(required=True))
    ruta_por_guia              = graphene.Field(RutaType, numero_guia=graphene.String(required=True))
    rutas_completas_por_estado = graphene.List(RutaType, estado=graphene.String(required=True))
    todas_rutas                = graphene.List(RutaType)

    def resolve_ruta(self, info, id):
        return Ruta.objects.get(id=id)

    @login_required
    def resolve_mis_rutas(self, info):
        user      = info.context.user
        conductor = Chofer.objects.get(usuario=user)
        return Ruta.objects.filter(conductor=conductor)

    @login_required
    def resolve_mis_rutas_por_estado(self, info, estado):
        user      = info.context.user
        conductor = Chofer.objects.get(usuario=user)
        return Ruta.objects.filter(conductor=conductor, estado=estado)

    def resolve_ruta_por_guia(self, info, numero_guia):
        try:
            return Ruta.objects.get(entregas__paquete__numero_guia=numero_guia)
        except Ruta.DoesNotExist:
            return None

    def resolve_rutas_completas_por_estado(self, info, estado):
        return Ruta.objects.filter(estado=estado)

    def resolve_todas_rutas(self, info):
        return Ruta.objects.all()


# ──────────────────────────────────────────────────────────────────────────────
# 7) RootQuery, RootMutation y RootSubscription
#    combinan tus módulos de paquete/entrega con Ruta
# ──────────────────────────────────────────────────────────────────────────────
class RootQuery(
    paquete_schema.Query,
    entrega_schema.Query,
    RutaQuery,
    graphene.ObjectType
):
    pass

class RootMutation(
    paquete_schema.Mutation,
    graphene.ObjectType
):
    crear_ruta          = CrearRuta.Field()
    cambiar_estado_ruta = CambiarEstadoRuta.Field()

class RootSubscription(graphene.ObjectType):
    ruta_por_estado = RutaPorEstadoSubscription.Field()
    todas_rutas     = TodasRutasSubscription.Field()


# ──────────────────────────────────────────────────────────────────────────────
# 8) Schema final
# ──────────────────────────────────────────────────────────────────────────────
schema = graphene.Schema(
    query        = RootQuery,
    mutation     = RootMutation,
    subscription = RootSubscription,
    types        = [
        producto_schema.ProductoType,
        paquete_schema.PaqueteType,
        entrega_schema.EntregaType,
        RutaType,
    ]
)

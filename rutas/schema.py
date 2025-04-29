# api_logix/schema.py

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
# 1) Imports de Graphene y modelos
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
# 2) Imports de esquemas parciales (todos independientes)
# ──────────────────────────────────────────────────────────────────────────────
import users.schema               as users_schema
import sensoresRuta.schema        as sensoresruta_schema
import fcm.schema                 as fcm_schema
import rutas.schema               as rutas_schema
import camiones.schema            as camiones_schema
import entrega.schema             as entrega_schema
import paquete.schema             as paquete_schema
import producto.schema            as producto_schema
import destinatario.schema        as destinatario_schema
import cliente.schema             as cliente_schema
import chofer.schema              as chofer_schema
import horarios.schema            as horarios_schema
import centrodistribucion.schema  as centrodis_schema
import roles_y_permisos.schema    as rolesperm_schema
import tipoproductos.schema       as tiposprod_schema
import Ubicacion.schema           as ubicacion_schema
import calcularenvio.schema       as calcularenvio_schema


# ──────────────────────────────────────────────────────────────────────────────
# 3) Tipo GraphQL para Ruta
# ──────────────────────────────────────────────────────────────────────────────
class RutaType(DjangoObjectType):
    class Meta:
        model  = Ruta
        fields = "__all__"


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

        # envío de notificación FCM
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

        try:
            device = FCMDevice.objects.get(user=ruta.conductor.usuario)
            enviar_notificacion_fcm_v1(
                token = device.token,
                title = "Ruta Actualizada",
                body  = f"Ruta {ruta_id} cambió a '{nuevo_estado}'."
            )
        except FCMDevice.DoesNotExist:
            print("Chofer sin token FCM.")

        RutaPorEstadoSubscription.broadcast_ruta(ruta)
        TodasRutasSubscription.broadcast_ruta(ruta)

        return CambiarEstadoRuta(ruta=ruta)


# ──────────────────────────────────────────────────────────────────────────────
# 6) Root Query (solo independientes), ObjectType al final
# ──────────────────────────────────────────────────────────────────────────────
class Query(
    users_schema.Query,
    sensoresruta_schema.Query,
    fcm_schema.Query,
    rutas_schema.Query,
    camiones_schema.Query,
    entrega_schema.Query,
    paquete_schema.Query,
    producto_schema.Query,
    destinatario_schema.Query,
    cliente_schema.Query,
    chofer_schema.Query,
    horarios_schema.Query,
    centrodis_schema.Query,
    rolesperm_schema.Query,
    tiposprod_schema.Query,
    ubicacion_schema.Query,
    calcularenvio_schema.Query,
    graphene.ObjectType,
):
    """Combina aquí **solamente** los Query independientes de cada app."""
    pass


# ──────────────────────────────────────────────────────────────────────────────
# 7) Root Mutation (igual que Query)
# ──────────────────────────────────────────────────────────────────────────────
class Mutation(
    users_schema.Mutation,
    sensoresruta_schema.Mutation,
    fcm_schema.Mutation,
    rutas_schema.Mutation,
    camiones_schema.Mutation,
    entrega_schema.Mutation,
    paquete_schema.Mutation,
    producto_schema.Mutation,
    destinatario_schema.Mutation,
    cliente_schema.Mutation,
    chofer_schema.Mutation,
    horarios_schema.Mutation,
    centrodis_schema.Mutation,
    rolesperm_schema.Mutation,
    tiposprod_schema.Mutation,
    ubicacion_schema.Mutation,
    calcularenvio_schema.Mutation,
    graphene.ObjectType,
):
    """Combina aquí las Mutations de cada app."""
    pass


# ──────────────────────────────────────────────────────────────────────────────
# 8) Root Subscription (solo las tuyas + las de apps que definan Subscriptions)
# ──────────────────────────────────────────────────────────────────────────────
class Subscription(
    rutas_schema.Subscription,
    # si hay otras apps con Subscription, añádelas aquí...
    graphene.ObjectType,
):
    pass


# ──────────────────────────────────────────────────────────────────────────────
# 9) Construcción final del Schema
# ──────────────────────────────────────────────────────────────────────────────
schema = graphene.Schema(
    query        = Query,
    mutation     = Mutation,
    subscription = Subscription,
    types        = [
        producto_schema.ProductoType,
        paquete_schema.PaqueteType,
        entrega_schema.EntregaType,
        RutaType,
    ]
)

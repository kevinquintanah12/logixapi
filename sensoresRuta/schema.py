# schema.py

# ——————————————————————————————————————————————————————————————
# 0) Parche temporal: envolver corutinas en tareas para asyncio.wait
# ——————————————————————————————————————————————————————————————
import asyncio

_original_wait = asyncio.wait

async def _patched_wait(aws, *args, **kwargs):
    loop = asyncio.get_event_loop()
    wrapped = [
        loop.create_task(a) if asyncio.iscoroutine(a) else a
        for a in aws
    ]
    return await _original_wait(wrapped, *args, **kwargs)

asyncio.wait = _patched_wait  # parchea en runtime


# ——————————————————————————————————————————————————————————————
# 1) Imports
# ——————————————————————————————————————————————————————————————
import graphene
from graphene_django.types import DjangoObjectType
from channels_graphql_ws import Subscription
from asgiref.sync import async_to_sync

from graphql_jwt.decorators import login_required

from .models           import Ruta, SensorRuta
from chofer.models     import Chofer
from camiones.models   import Camion
from entrega.models    import Entrega
from paquete.models    import Paquete
from rutas.models      import Ruta as RutaModel
from fcm.firebase_config import enviar_notificacion_fcm_v1
from fcm.models          import FCMDevice
from rutas.schema import RutaType


# ——————————————————————————————————————————————————————————————
# 2) Tipos GraphQL
# ——————————————————————————————————————————————————————————————
class SensorRutaType(DjangoObjectType):
    class Meta:
        model = SensorRuta
        fields = "__all__"


# ——————————————————————————————————————————————————————————————
# 3) Subscriptions
# ——————————————————————————————————————————————————————————————
class RutaPorEstadoSubscription(Subscription):
    ruta   = graphene.Field(RutaType)
    estado = graphene.String()

    class Arguments:
        estado = graphene.String(required=True)

    def subscribe(self, info, estado):
        return [estado]

    @classmethod
    def publish(cls, payload, info, estado):
        ruta_obj = payload.get("ruta")
        return cls(ruta=ruta_obj, estado=estado)

    @classmethod
    def broadcast_ruta(cls, ruta_obj):
        async_to_sync(cls.broadcast)(
            group   = ruta_obj.estado,
            payload = {"ruta": ruta_obj, "estado": ruta_obj.estado},
        )


class MisRutasPorEstadoSubscription(Subscription):
    ruta   = graphene.Field(RutaType)
    estado = graphene.String()

    class Arguments:
        estado = graphene.String(required=True)

    @login_required
    def subscribe(self, info, estado):
        user = info.context.user
        return [f"mis_rutas_{user.id}_{estado}"]

    @classmethod
    def publish(cls, payload, info, estado):
        ruta_obj = payload.get("ruta")
        user     = info.context.user
        if ruta_obj.conductor.usuario.id == user.id:
            return cls(ruta=ruta_obj, estado=estado)
        return None

    @classmethod
    def broadcast_mis_rutas(cls, ruta_obj):
        user_id = ruta_obj.conductor.usuario.id
        group = f"mis_rutas_{user_id}_{ruta_obj.estado}"
        async_to_sync(cls.broadcast)(
            group=group,
            payload={"ruta": ruta_obj, "estado": ruta_obj.estado}
        )


class SensorRutaPorRutaSubscription(Subscription):
    sensor = graphene.Field(SensorRutaType)

    class Arguments:
        ruta_id = graphene.ID(required=True)

    def subscribe(self, info, ruta_id):
        return [f"sensor_ruta_{ruta_id}"]

    @classmethod
    def publish(cls, payload, info, ruta_id):
        sensor_obj = payload.get("sensor")
        return cls(sensor=sensor_obj)

    @classmethod
    def broadcast_sensor(cls, sensor_obj):
        async_to_sync(cls.broadcast)(
            group   = f"sensor_ruta_{sensor_obj.ruta.id}",
            payload = {"sensor": sensor_obj},
        )


# ——————————————————————————————————————————————————————————————
# 4) Mutations (creación + emite)
# ——————————————————————————————————————————————————————————————
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

    def mutate(
        self, info,
        distancia, prioridad, conductor_id, vehiculo_id,
        fecha_inicio, fecha_fin, estado, entrega_id
    ):
        vehiculo  = Camion.objects.get(id=vehiculo_id)
        conductor = Chofer.objects.get(id=conductor_id)
        entrega   = Entrega.objects.get(id=entrega_id)

        ruta = RutaModel.objects.create(
            distancia    = distancia,
            prioridad    = prioridad,
            conductor    = conductor,
            vehiculo     = vehiculo,
            fecha_inicio = fecha_inicio,
            fecha_fin    = fecha_fin,
            estado       = estado,
        )
        ruta.entregas.add(entrega)

        try:
            device = FCMDevice.objects.get(user=conductor.usuario)
            enviar_notificacion_fcm_v1(
                token = device.token,
                title = "Nueva Ruta Asignada",
                body  = "Tienes una ruta nueva."
            )
        except FCMDevice.DoesNotExist:
            print("Chofer sin token FCM.")

        RutaPorEstadoSubscription.broadcast_ruta(ruta)
        MisRutasPorEstadoSubscription.broadcast_mis_rutas(ruta)

        return CrearRuta(ruta=ruta)


class CambiarEstadoRuta(graphene.Mutation):
    class Arguments:
        ruta_id      = graphene.Int(required=True)
        nuevo_estado = graphene.String(required=True)

    ruta = graphene.Field(RutaType)

    def mutate(self, info, ruta_id, nuevo_estado):
        ruta = RutaModel.objects.get(id=ruta_id)
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
        MisRutasPorEstadoSubscription.broadcast_mis_rutas(ruta)

        return CambiarEstadoRuta(ruta=ruta)


class CrearSensorRuta(graphene.Mutation):
    class Arguments:
        ruta_id     = graphene.ID(required=True)
        latitud     = graphene.Float(required=True)
        longitud    = graphene.Float(required=True)
        temperatura = graphene.Float(required=True)
        humedad     = graphene.Float(required=True)

    sensor = graphene.Field(SensorRutaType)

    def mutate(self, info, ruta_id, latitud, longitud, temperatura, humedad):
        ruta = RutaModel.objects.get(id=ruta_id)
        sensor = SensorRuta.objects.create(
            ruta        = ruta,
            latitud     = latitud,
            longitud    = longitud,
            temperatura = temperatura,
            humedad     = humedad
        )
        SensorRutaPorRutaSubscription.broadcast_sensor(sensor)
        return CrearSensorRuta(sensor=sensor)


# ——————————————————————————————————————————————————————————————
# 5) Queries
# ——————————————————————————————————————————————————————————————
class Query(graphene.ObjectType):
    ruta                       = graphene.Field(RutaType, id=graphene.Int(required=True))
    mis_rutas                  = graphene.List(RutaType)
    mis_rutas_por_estado       = graphene.List(RutaType, estado=graphene.String(required=True))
    ruta_por_guia              = graphene.Field(RutaType, numero_guia=graphene.String(required=True))
    rutas_completas_por_estado = graphene.List(RutaType, estado=graphene.String(required=True))
    sensores_por_ruta          = graphene.List(SensorRutaType, ruta_id=graphene.ID(required=True))

    # Nueva query para obtener todos los sensores
    todos_los_sensores         = graphene.List(SensorRutaType)

    def resolve_ruta(self, info, id):
        return RutaModel.objects.get(id=id)

    @login_required
    def resolve_mis_rutas(self, info):
        user      = info.context.user
        conductor = Chofer.objects.get(usuario=user)
        return RutaModel.objects.filter(conductor=conductor)

    @login_required
    def resolve_mis_rutas_por_estado(self, info, estado):
        user      = info.context.user
        conductor = Chofer.objects.get(usuario=user)
        return RutaModel.objects.filter(conductor=conductor, estado=estado)

    def resolve_ruta_por_guia(self, info, numero_guia):
        try:
            return RutaModel.objects.get(entregas__paquete__numero_guia=numero_guia)
        except RutaModel.DoesNotExist:
            return None

    def resolve_rutas_completas_por_estado(self, info, estado):
        return RutaModel.objects.filter(estado=estado)

    def resolve_sensores_por_ruta(self, info, ruta_id):
        return SensorRuta.objects.filter(ruta_id=ruta_id).order_by('-timestamp')

    # Resolver de la nueva consulta
    def resolve_todos_los_sensores(self, info):
        return SensorRuta.objects.all().order_by('-timestamp')


# ——————————————————————————————————————————————————————————————
# 6) Roots
# ——————————————————————————————————————————————————————————————
class Mutation(graphene.ObjectType):
    crear_ruta          = CrearRuta.Field()
    cambiar_estado_ruta = CambiarEstadoRuta.Field()
    crear_sensor_ruta   = CrearSensorRuta.Field()


class Subscription(graphene.ObjectType):
    ruta_por_estado      = RutaPorEstadoSubscription.Field()
    mis_rutas_por_estado = MisRutasPorEstadoSubscription.Field()
    sensor_por_ruta      = SensorRutaPorRutaSubscription.Field()


# ——————————————————————————————————————————————————————————————
# 7) Schema
# ——————————————————————————————————————————————————————————————
schema = graphene.Schema(
    query        = Query,
    mutation     = Mutation,
    subscription = Subscription,
)

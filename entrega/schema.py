# subscriptions.py

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

from .models import Entrega
from paquete.models import Paquete


# ——————————————
# 2. Tipos GraphQL
# ——————————————
class EntregaType(DjangoObjectType):
    class Meta:
        model = Entrega
        fields = "__all__"

class PaqueteType(DjangoObjectType):
    class Meta:
        model = Paquete
        fields = "__all__"


# ——————————————————————————
# 3. Subscription: entregas por estado
# ——————————————————————————
class EntregaPorEstadoSubscription(Subscription):
    """
    Emite una Entrega cada vez que cambia su estado o se crea.
    """

    entrega = graphene.Field(EntregaType)
    estado = graphene.String()

    class Arguments:
        estado = graphene.String(required=True)

    def subscribe(self, info, estado):
        # Nos unimos al grupo con el nombre del estado
        return [estado]

    @classmethod
    def publish(cls, payload, info, estado):
        # payload viene de broadcast_entrega()
        entrega_obj = payload.get("entrega")
        return cls(entrega=entrega_obj, estado=estado)

    @classmethod
    def broadcast_entrega(cls, entrega_obj):
        # Llama al broadcast() en el contexto adecuado
        async_to_sync(cls.broadcast)(
            group=entrega_obj.estado,
            payload={"entrega": entrega_obj, "estado": entrega_obj.estado},
        )


# ——————————————————————————
# 4. Mutations (crea + emite)
# ——————————————————————————
class CrearEntrega(graphene.Mutation):
    class Arguments:
        paquete_id = graphene.Int(required=True)
        fecha_entrega = graphene.DateTime(required=True)
        estado = graphene.String(required=True)
        pin = graphene.String(required=True)

    entrega = graphene.Field(EntregaType)

    def mutate(self, info, paquete_id, fecha_entrega, estado, pin):
        paquete = Paquete.objects.get(id=paquete_id)
        entrega = Entrega.objects.create(
            paquete=paquete,
            fecha_entrega=fecha_entrega,
            estado=estado,
            pin=pin,
        )
        EntregaPorEstadoSubscription.broadcast_entrega(entrega)
        return CrearEntrega(entrega=entrega)


class FinalizarEntrega(graphene.Mutation):
    class Arguments:
        entrega_id = graphene.Int(required=True)
        pin = graphene.String(required=True)
        estado = graphene.String(required=True)

    entrega = graphene.Field(EntregaType)
    error = graphene.String()

    def mutate(self, info, entrega_id, pin, estado):
        entrega = Entrega.objects.get(id=entrega_id)
        if entrega.pin != pin:
            return FinalizarEntrega(error="PIN incorrecto")
        entrega.estado = estado
        entrega.save()
        EntregaPorEstadoSubscription.broadcast_entrega(entrega)
        return FinalizarEntrega(entrega=entrega)


class EliminarTodasEntregas(graphene.Mutation):
    success = graphene.Boolean()

    def mutate(self, info):
        Entrega.objects.all().delete()
        return EliminarTodasEntregas(success=True)


class EliminarEntregaPorId(graphene.Mutation):
    class Arguments:
        id = graphene.Int(required=True)

    success = graphene.Boolean()
    error = graphene.String()

    def mutate(self, info, id):
        try:
            Entrega.objects.get(id=id).delete()
            return EliminarEntregaPorId(success=True)
        except Entrega.DoesNotExist:
            return EliminarEntregaPorId(success=False, error="Entrega no encontrada")


class ActualizarEstadoEntrega(graphene.Mutation):
    class Arguments:
        entrega_id = graphene.Int(required=True)
        estado = graphene.String(required=True)

    entrega = graphene.Field(EntregaType)
    error = graphene.String()

    def mutate(self, info, entrega_id, estado):
        try:
            entrega = Entrega.objects.get(id=entrega_id)
        except Entrega.DoesNotExist:
            return ActualizarEstadoEntrega(error="Entrega no encontrada")
        entrega.estado = estado
        entrega.save()
        EntregaPorEstadoSubscription.broadcast_entrega(entrega)
        return ActualizarEstadoEntrega(entrega=entrega)


# ——————————————————————
# 5. Queries
# ——————————————————————
class Query(graphene.ObjectType):
    entrega = graphene.Field(EntregaType, id=graphene.Int(required=True))
    entrega_por_guia = graphene.Field(
        EntregaType, numero_guia=graphene.String(required=True)
    )
    entregas_por_estado = graphene.List(
        EntregaType, estado=graphene.String(required=True)
    )
    entregas_por_paquete = graphene.List(
        EntregaType, paquete_id=graphene.Int(required=True)
    )
    entregas_por_fecha = graphene.List(
        EntregaType, fecha_entrega=graphene.DateTime(required=True)
    )
    entregas_por_ciudad_estado = graphene.List(
        EntregaType,
        ciudad=graphene.String(required=True),
        estado=graphene.String(required=True),
    )
    mis_entregas_en_proceso = graphene.List(EntregaType)
    entregas = graphene.List(EntregaType)

    def resolve_entrega(self, info, id):
        return Entrega.objects.get(id=id)

    def resolve_entrega_por_guia(self, info, numero_guia):
        return Entrega.objects.get(paquete__numero_guia=numero_guia)

    def resolve_entregas_por_estado(self, info, estado):
        return Entrega.objects.filter(estado=estado)

    def resolve_entregas_por_paquete(self, info, paquete_id):
        return Entrega.objects.filter(paquete_id=paquete_id)

    def resolve_entregas_por_fecha(self, info, fecha_entrega):
        return Entrega.objects.filter(fecha_entrega=fecha_entrega)

    def resolve_entregas_por_ciudad_estado(self, info, ciudad, estado):
        return Entrega.objects.filter(
            destinatario__ciudad=ciudad,
            destinatario__estado=estado
        )

    def resolve_mis_entregas_en_proceso(self, info):
        return Entrega.objects.filter(estado="En proceso")

    def resolve_entregas(self, info):
        return Entrega.objects.all()


# ——————————————————————
# 6. Schema root
# ——————————————————————
class Mutation(graphene.ObjectType):
    crear_entrega = CrearEntrega.Field()
    finalizar_entrega = FinalizarEntrega.Field()
    eliminar_todas_entregas = EliminarTodasEntregas.Field()
    eliminar_entrega_por_id = EliminarEntregaPorId.Field()
    actualizar_estado_entrega = ActualizarEstadoEntrega.Field()

class SubscriptionRoot(graphene.ObjectType):
    entrega_por_estado = EntregaPorEstadoSubscription.Field()

schema = graphene.Schema(
    query=Query,
    mutation=Mutation,
    subscription=SubscriptionRoot,
)

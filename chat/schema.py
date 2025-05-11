# -*- coding: utf-8 -*-
# Chat privado por cliente en Graphene + Django con cola dinámica

import asyncio
from threading import Lock
_original_wait = asyncio.wait

async def _patched_wait(aws, *args, **kwargs):
    loop = asyncio.get_event_loop()
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

from .models import Mensaje

# Conjunto global de clientes activos
_ACTIVE_CLIENTS: set[str] = set()
_LOCK = Lock()

# 1) Tipo de mensaje
class MensajeType(DjangoObjectType):
    class Meta:
        model = Mensaje
        fields = "__all__"

# 2) Suscripción privada por cliente
class PrivateChatSubscription(Subscription):
    mensaje = graphene.Field(MensajeType)

    class Arguments:
        nombre = graphene.String(required=True)

    def subscribe(self, info, nombre):
        # Añadir el cliente al set de activos
        with _LOCK:
            _ACTIVE_CLIENTS.add(nombre)
        return [f"chat_{nombre}"]

    @classmethod
    def publish(cls, payload, info, nombre):
        return cls(mensaje=payload["mensaje"])

    @classmethod
    def broadcast_mensaje(cls, mensaje, nombre):
        async_to_sync(cls.broadcast)(
            group=f"chat_{nombre}",
            payload={"mensaje": mensaje},
        )

    def unsubscribe(self, info, nombre):
        # Cuando el cliente cierra la conexión, lo removemos
        with _LOCK:
            _ACTIVE_CLIENTS.discard(nombre)
        super().unsubscribe(info, nombre)

# 3) Mutación pública que usa canal privado
class EnviarMensajePublico(graphene.Mutation):
    class Arguments:
        nombre = graphene.String(required=True)
        contenido = graphene.String(required=True)

    mensaje = graphene.Field(MensajeType)

    def mutate(self, info, nombre, contenido):
        mensaje = Mensaje.objects.create(
            nombre=nombre,
            contenido=contenido
        )
        PrivateChatSubscription.broadcast_mensaje(mensaje, nombre)
        return EnviarMensajePublico(mensaje=mensaje)

# 4) Query de historial por cliente
class Query(graphene.ObjectType):
    mensajes = graphene.List(
        MensajeType,
        nombre=graphene.String(required=True)
    )
    clientes_activos = graphene.List(graphene.String)

    def resolve_mensajes(self, info, nombre):
        return Mensaje.objects.filter(
            nombre=nombre
        ).order_by("timestamp")

    def resolve_clientes_activos(self, info):
        # Devolver la lista actual de clientes en cola
        with _LOCK:
            return list(_ACTIVE_CLIENTS)

# 5) Registrar mutaciones y suscripciones
class Mutation(graphene.ObjectType):
    enviar_mensaje_publico = EnviarMensajePublico.Field()

class SubscriptionRoot(graphene.ObjectType):
    private_chat = PrivateChatSubscription.Field()

# 6) Crear esquema
schema = graphene.Schema(
    query=Query,
    mutation=Mutation,
    subscription=SubscriptionRoot
)

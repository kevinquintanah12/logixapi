# -*- coding: utf-8 -*-
# Chat público en Graphene + Django

import asyncio
_original_wait = asyncio.wait
async def _patched_wait(aws, *args, **kwargs):
    loop = asyncio.get_event_loop()
    wrapped = [loop.create_task(a) if asyncio.iscoroutine(a) else a for a in aws]
    return await _original_wait(wrapped, *args, **kwargs)
asyncio.wait = _patched_wait

import graphene
from graphene_django.types import DjangoObjectType
from channels_graphql_ws import Subscription
from asgiref.sync import async_to_sync

from .models import Mensaje

# Tipado del mensaje
class MensajeType(DjangoObjectType):
    class Meta:
        model = Mensaje
        fields = "__all__"

# Suscripción pública
class PublicChatSubscription(Subscription):
    mensaje = graphene.Field(MensajeType)

    def subscribe(self, info):
        return ["public_channel"]

    @classmethod
    def publish(cls, payload, info):
        return cls(mensaje=payload["mensaje"])

    @classmethod
    def broadcast_mensaje(cls, mensaje):
        async_to_sync(cls.broadcast)(
            group="public_channel",
            payload={"mensaje": mensaje},
        )

# Mutación pública (sin login)
class EnviarMensajePublico(graphene.Mutation):
    class Arguments:
        nombre = graphene.String(required=False)
        contenido = graphene.String(required=True)

    mensaje = graphene.Field(MensajeType)

    def mutate(self, info, contenido, nombre=None):
        mensaje = Mensaje.objects.create(
            nombre=nombre or "Anónimo",
            contenido=contenido
        )
        PublicChatSubscription.broadcast_mensaje(mensaje)
        return EnviarMensajePublico(mensaje=mensaje)

# Consulta de mensajes públicos
class Query(graphene.ObjectType):
    mensajes = graphene.List(MensajeType)

    def resolve_mensajes(self, info):
        return Mensaje.objects.all().order_by("-timestamp")[:50]

# Mutaciones disponibles
class Mutation(graphene.ObjectType):
    enviar_mensaje_publico = EnviarMensajePublico.Field()

# Suscripciones disponibles
class SubscriptionRoot(graphene.ObjectType):
    public_chat = PublicChatSubscription.Field()

# Esquema final
schema = graphene.Schema(
    query=Query,
    mutation=Mutation,
    subscription=SubscriptionRoot
)

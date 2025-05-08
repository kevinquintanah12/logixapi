# -*- coding: utf-8 -*-
# Servicio de Chat y Soporte en Graphene + Django

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
from graphql_jwt.decorators import login_required
from django.db import models
from django.contrib.auth.models import User
from .models import Mensaje

class MensajeType(DjangoObjectType):
    class Meta:
        model = Mensaje
        fields = "__all__"

class ChatSubscription(Subscription):
    mensaje = graphene.Field(MensajeType)
    class Arguments:
        usuario_id = graphene.Int(required=True)
    def subscribe(self, info, usuario_id):
        return [f"user_{usuario_id}"]
    @classmethod
    def publish(cls, payload, info, usuario_id):
        return cls(mensaje=payload["mensaje"])
    @classmethod
    def broadcast_mensaje(cls, mensaje):
        async_to_sync(cls.broadcast)(
            group=f"user_{mensaje.receptor.id}",
            payload={"mensaje": mensaje},
        )

class SupportSubscription(Subscription):
    mensaje = graphene.Field(MensajeType)
    def subscribe(self, info):
        return ["support"]
    @classmethod
    def publish(cls, payload, info):
        return cls(mensaje=payload["mensaje"])
    @classmethod
    def broadcast_support(cls, mensaje):
        async_to_sync(cls.broadcast)(
            group="support",
            payload={"mensaje": mensaje},
        )

class EnviarMensaje(graphene.Mutation):
    class Arguments:
        receptor_id = graphene.Int(required=True)
        contenido = graphene.String(required=True)
    mensaje = graphene.Field(MensajeType)

    @login_required
    def mutate(self, info, receptor_id, contenido):
        emisor = info.context.user
        receptor = User.objects.get(id=receptor_id)
        mensaje = Mensaje.objects.create(
            emisor=emisor, receptor=receptor, contenido=contenido
        )
        ChatSubscription.broadcast_mensaje(mensaje)
        return EnviarMensaje(mensaje=mensaje)

class SolicitarSoporte(graphene.Mutation):
    class Arguments:
        contenido = graphene.String(required=True)
    mensaje = graphene.Field(MensajeType)

    @login_required
    def mutate(self, info, contenido):
        cliente = info.context.user
        # Asignar un receptor genérico (primer staff encontrado)
        receptor = User.objects.filter(is_staff=True).first()
        mensaje = Mensaje.objects.create(
            emisor=cliente, receptor=receptor, contenido=contenido
        )
        SupportSubscription.broadcast_support(mensaje)
        return SolicitarSoporte(mensaje=mensaje)

class Query(graphene.ObjectType):
    mensajes_entre_usuarios = graphene.List(
        MensajeType,
        usuario_id=graphene.Int(required=True)
    )

    @login_required
    def resolve_mensajes_entre_usuarios(self, info, usuario_id):
        user = info.context.user
        return Mensaje.objects.filter(
            models.Q(emisor=user, receptor_id=usuario_id) |
            models.Q(emisor_id=usuario_id, receptor=user)
        ).order_by("timestamp")

class Mutation(graphene.ObjectType):
    enviar_mensaje = EnviarMensaje.Field()
    solicitar_soporte = SolicitarSoporte.Field()

class SubscriptionRoot(graphene.ObjectType):
    chat = ChatSubscription.Field()
    support = SupportSubscription.Field()

schema = graphene.Schema(
    query=Query,
    mutation=Mutation,
    subscription=SubscriptionRoot
)

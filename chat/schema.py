# -*- coding: utf-8 -*-
# Servicio de Chat y Soporte en Graphene + Django

import asyncio
import random

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
from django.contrib.auth.models import User, Group
from django.db import models

from .models import Mensaje

# Tipado de Mensaje para Graphene
class MensajeType(DjangoObjectType):
    class Meta:
        model = Mensaje
        fields = "__all__"

# Suscripción de chat entre dos usuarios
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

# Suscripción general de soporte (grupo)
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

# Mutación para enviar mensaje directo
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
            emisor=emisor,
            receptor=receptor,
            contenido=contenido
        )
        ChatSubscription.broadcast_mensaje(mensaje)
        return EnviarMensaje(mensaje=mensaje)

# Mutación para solicitar soporte a un grupo de agentes
class SolicitarSoporte(graphene.Mutation):
    class Arguments:
        contenido = graphene.String(required=True)

    mensaje = graphene.Field(MensajeType)

    @login_required
    def mutate(self, info, contenido):
        cliente = info.context.user
        # Obtener o crear el grupo de soporte
        grupo_soporte, _ = Group.objects.get_or_create(name="soporte")
        agentes = list(grupo_soporte.user_set.all())
        if not agentes:
            raise Exception("No hay agentes de soporte disponibles en el grupo 'soporte'.")
        # Seleccionar un agente aleatorio del grupo
        receptor = random.choice(agentes)

        mensaje = Mensaje.objects.create(
            emisor=cliente,
            receptor=receptor,
            contenido=contenido
        )
        # Broadcast a todos suscriptores de soporte
        SupportSubscription.broadcast_support(mensaje)
        return SolicitarSoporte(mensaje=mensaje)

# Consultas para obtener mensajes
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

# Punto de entrada de Mutaciones
class Mutation(graphene.ObjectType):
    enviar_mensaje = EnviarMensaje.Field()
    solicitar_soporte = SolicitarSoporte.Field()

# Punto de entrada de Suscripciones
class SubscriptionRoot(graphene.ObjectType):
    chat = ChatSubscription.Field()
    support = SupportSubscription.Field()

# Definición del esquema completo
schema = graphene.Schema(
    query=Query,
    mutation=Mutation,
    subscription=SubscriptionRoot
)

# -*- coding: utf-8 -*-
import asyncio
from threading import Lock
import graphene
from graphene_django.types import DjangoObjectType
from channels_graphql_ws import Subscription
from asgiref.sync import async_to_sync
from .models import Mensaje

# Estado global
_ACTIVE_CLIENTS: set[str] = set()
_LOCK = Lock()

class MensajeType(DjangoObjectType):
    class Meta:
        model = Mensaje
        fields = "__all__"

# — Suscripción para la cola de clientes —
class ActiveClientsSubscription(Subscription):
    nombre = graphene.String()
    action = graphene.String()  # "join" o "leave"

    def subscribe(self, info):
        return ["active_clients"]

    @classmethod
    def publish(cls, payload, info):
        return cls(nombre=payload["nombre"], action=payload["action"])

    @classmethod
    def broadcast_event(cls, nombre: str, action: str):
        async_to_sync(cls.broadcast)(
            group="active_clients",
            payload={"nombre": nombre, "action": action},
        )

# — Suscripción privada por cliente —
class PrivateChatSubscription(Subscription):
    mensaje = graphene.Field(MensajeType)

    class Arguments:
        nombre = graphene.String(required=True)

    def subscribe(self, info, nombre):
        # Cuando un cliente se suscribe, lo marcamos “activo”
        with _LOCK:
            first_time = nombre not in _ACTIVE_CLIENTS
            _ACTIVE_CLIENTS.add(nombre)
        if first_time:
            ActiveClientsSubscription.broadcast_event(nombre, "join")
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
        # Cuando un cliente cierra su canal privado, lo marcamos “inactivo”
        with _LOCK:
            if nombre in _ACTIVE_CLIENTS:
                _ACTIVE_CLIENTS.remove(nombre)
                ActiveClientsSubscription.broadcast_event(nombre, "leave")
        super().unsubscribe(info, nombre)

# — Mutación para enviar mensajes —
class EnviarMensajePublico(graphene.Mutation):
    class Arguments:
        nombre = graphene.String(required=True)
        contenido = graphene.String(required=True)

    mensaje = graphene.Field(MensajeType)

    def mutate(self, info, nombre, contenido):
        mensaje = Mensaje.objects.create(nombre=nombre, contenido=contenido)
        PrivateChatSubscription.broadcast_mensaje(mensaje, nombre)
        return EnviarMensajePublico(mensaje=mensaje)

# — Query opcional de historial —
class Query(graphene.ObjectType):
    mensajes = graphene.List(
        MensajeType,
        nombre=graphene.String(required=True)
    )

    def resolve_mensajes(self, info, nombre):
        return Mensaje.objects.filter(nombre=nombre).order_by("timestamp")

class Mutation(graphene.ObjectType):
    enviar_mensaje_publico = EnviarMensajePublico.Field()

class SubscriptionRoot(graphene.ObjectType):
    active_clients = ActiveClientsSubscription.Field()
    private_chat   = PrivateChatSubscription.Field()

schema = graphene.Schema(
    query=Query,
    mutation=Mutation,
    subscription=SubscriptionRoot
)

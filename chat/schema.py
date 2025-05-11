# -*- coding: utf-8 -*-
import asyncio
from threading import Lock
import graphene
from graphene_django.types import DjangoObjectType
from channels_graphql_ws import Subscription
from asgiref.sync import async_to_sync
from .models import Mensaje

# Estado global de clientes
_ACTIVE_CLIENTS: set[str] = set()
_LOCK = Lock()

# — Modelo Django esperado —  
# class Mensaje(models.Model):
#     remitente = models.CharField(max_length=100)
#     destinatario = models.CharField(max_length=100)
#     contenido = models.TextField()
#     timestamp = models.DateTimeField(auto_now_add=True)

class MensajeType(DjangoObjectType):
    class Meta:
        model = Mensaje
        fields = ("remitente", "destinatario", "contenido", "timestamp")

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
        nombre = graphene.String(required=True)  # nombre del destinatario

    def subscribe(self, info, nombre):
        with _LOCK:
            first_time = nombre not in _ACTIVE_CLIENTS
            _ACTIVE_CLIENTS.add(nombre)
        if first_time:
            ActiveClientsSubscription.broadcast_event(nombre, "join")
        return [f"chat_{nombre}"]

    @classmethod
    def publish(cls, payload, info, nombre):
        # Solo publicamos mensajes cuyo destinatario coincida
        return cls(mensaje=payload["mensaje"])

    @classmethod
    def broadcast_mensaje(cls, mensaje_obj):
        dest = mensaje_obj.destinatario
        async_to_sync(cls.broadcast)(
            group=f"chat_{dest}",
            payload={"mensaje": mensaje_obj},
        )

    def unsubscribe(self, info, nombre):
        with _LOCK:
            if nombre in _ACTIVE_CLIENTS:
                _ACTIVE_CLIENTS.remove(nombre)
                ActiveClientsSubscription.broadcast_event(nombre, "leave")
        super().unsubscribe(info, nombre)

# — Mutación para enviar mensajes —
class EnviarMensajePublico(graphene.Mutation):
    class Arguments:
        destinatario = graphene.String(required=True)
        contenido = graphene.String(required=True)

    mensaje = graphene.Field(MensajeType)

    def mutate(self, info, destinatario, contenido):
        remitente = info.context.user.username if info.context.user else "Admin"
        mensaje = Mensaje.objects.create(
            remitente=remitente,
            destinatario=destinatario,
            contenido=contenido
        )
        PrivateChatSubscription.broadcast_mensaje(mensaje)
        return EnviarMensajePublico(mensaje=mensaje)

# — Query para historial y clientes activos —
class Query(graphene.ObjectType):
    mensajes = graphene.List(
        MensajeType,
        nombre=graphene.String(required=True)  # aquí 'nombre' es el destinatario
    )
    clientes_activos = graphene.List(graphene.String)

    def resolve_mensajes(self, info, nombre):
        return Mensaje.objects.filter(destinatario=nombre).order_by("timestamp")

    def resolve_clientes_activos(self, info):
        with _LOCK:
            return list(_ACTIVE_CLIENTS)

# — Mutaciones —
class Mutation(graphene.ObjectType):
    enviar_mensaje_publico = EnviarMensajePublico.Field()

# — Suscripciones —
class SubscriptionRoot(graphene.ObjectType):
    active_clients = ActiveClientsSubscription.Field()
    private_chat = PrivateChatSubscription.Field()

# — Esquema principal —
schema = graphene.Schema(
    query=Query,
    mutation=Mutation,
    subscription=SubscriptionRoot
)

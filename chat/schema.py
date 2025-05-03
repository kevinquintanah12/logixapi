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
from django.db import models
from django.contrib.auth.models import User

from .models import Mensaje

# ——————————————————————————————————————————————————————————————
# 2) Tipo GraphQL para Mensaje
# ——————————————————————————————————————————————————————————————
class MensajeType(DjangoObjectType):
    class Meta:
        model = Mensaje
        fields = "__all__"

# ——————————————————————————————————————————————————————————————
# 3) Subscription: chat individual por usuario
# ——————————————————————————————————————————————————————————————
class ChatSubscription(Subscription):
    """
    Emite un Mensaje cada vez que un usuario recibe uno nuevo.
    """
    mensaje = graphene.Field(MensajeType)

    class Arguments:
        usuario_id = graphene.Int(required=True)

    def subscribe(self, info, usuario_id):
        # Suscríbete al canal para el receptor
        return [f"user_{usuario_id}"]

    @classmethod
    def publish(cls, payload, info, usuario_id):
        return cls(mensaje=payload["mensaje"])

    @classmethod
    def broadcast_mensaje(cls, mensaje):
        receptor_group = f"user_{mensaje.receptor.id}"
        async_to_sync(cls.broadcast)(
            group=receptor_group,
            payload={"mensaje": mensaje},
        )

# ——————————————————————————————————————————————————————————————
# 4) Mutation para enviar mensaje
# ——————————————————————————————————————————————————————————————
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

        # Emitimos el mensaje a través de la suscripción
        ChatSubscription.broadcast_mensaje(mensaje)
        return EnviarMensaje(mensaje=mensaje)

# ——————————————————————————————————————————————————————————————
# 5) Consultas opcionales: historial de chat
# ——————————————————————————————————————————————————————————————
class Query(graphene.ObjectType):
    mensajes_entre_usuarios = graphene.List(
        MensajeType,
        usuario_id=graphene.Int(required=True)
    )

    @login_required
    def resolve_mensajes_entre_usuarios(self, info, usuario_id):
        user = info.context.user
        # Trae mensajes entre el usuario autenticado y otro usuario
        return Mensaje.objects.filter(
            models.Q(emisor=user, receptor_id=usuario_id) |
            models.Q(emisor_id=usuario_id, receptor=user)
        ).order_by("timestamp")

# ——————————————————————————————————————————————————————————————
# 6) Root de Mutations y Subscriptions
# ——————————————————————————————————————————————————————————————
class Mutation(graphene.ObjectType):
    enviar_mensaje = EnviarMensaje.Field()

class SubscriptionRoot(graphene.ObjectType):
    chat = ChatSubscription.Field()

# ——————————————————————————————————————————————————————————————
# 7) Schema final
# ——————————————————————————————————————————————————————————————
schema = graphene.Schema(
    query=Query,
    mutation=Mutation,
    subscription=SubscriptionRoot
)

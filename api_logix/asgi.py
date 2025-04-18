import os
import django

from django.core.asgi import get_asgi_application
from django.urls import path

from channels.routing import ProtocolTypeRouter, URLRouter
from channels.auth import AuthMiddlewareStack
from channels_graphql_ws import GraphqlWsConsumer

# ——————————————————————————————
# 1. Configuración de Django
# ——————————————————————————————
os.environ.setdefault("DJANGO_SETTINGS_MODULE", "api_logix.settings")
django.setup()

# ——————————————————————————————
# 2. Importa tu schema con Query, Mutation y Subscription
# ——————————————————————————————
from entrega.schema import schema
from rutas.schema import schema
# ——————————————————————————————
# 3. Define tu Consumer basado en channels_graphql_ws
# ——————————————————————————————
class MyGraphqlWsConsumer(GraphqlWsConsumer):
    # El consumer “apunta” a tu schema
    schema = schema

    async def on_connect(self, payload):
        # Aquí puedes validar JWT, cookies, etc.
        # Si devuelves False o lanzas excepción, la conexión se rechaza.
        return

# ——————————————————————————————
# 4. Define las rutas de WebSocket
# ——————————————————————————————
websocket_urlpatterns = [
    # En /graphql/ atenderemos queries, mutations y subscriptions por WS
    path("graphql/", MyGraphqlWsConsumer.as_asgi()),
]

# ——————————————————————————————
# 5. Construye la aplicación ASGI combinando HTTP + WebSocket
# ——————————————————————————————
application = ProtocolTypeRouter({
    # HTTP: Django (views, GraphQL over HTTP, etc.)
    "http": get_asgi_application(),

    # WebSocket: Channels + GraphQL WS
    "websocket": AuthMiddlewareStack(
        URLRouter(websocket_urlpatterns)
    ),
})

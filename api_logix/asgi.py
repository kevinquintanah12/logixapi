import os
import django

# ——————————————————————————————
# 1. Configuración de Django
# ——————————————————————————————
os.environ.setdefault("DJANGO_SETTINGS_MODULE", "api_logix.settings")
django.setup()


# ——————————————————————————————
# 2. Importaciones de ASGI, Channels y GraphQL
#    (haciéndolas después de django.setup())
# ——————————————————————————————
from django.core.asgi import get_asgi_application
from channels.routing import ProtocolTypeRouter, URLRouter
from channels.auth import AuthMiddlewareStack
from django.urls import path
from channels_graphql_ws import GraphqlWsConsumer

# Importa aquí tu schema. Si tienes varios, renómbralos o fusiónalos antes.
from entrega.schema import schema
from rutas.schema import schema  # solo si lo necesitas y lo combinas


# ——————————————————————————————
# 3. Define tu WebSocket Consumer
# ——————————————————————————————
class MyGraphqlWsConsumer(GraphqlWsConsumer):
    schema = schema  # apunta al schema importado

    async def on_connect(self, payload):
        """
        Aquí puedes validar tokens, cookies, etc.
        Si devuelves False o lanzas excepción, la conexión WS se rechazará.
        """
        return


# ——————————————————————————————
# 4. Rutas de WebSocket
# ——————————————————————————————
websocket_urlpatterns = [
    path("graphql/", MyGraphqlWsConsumer.as_asgi()),
]


# ——————————————————————————————
# 5. Aplicación ASGI combinada (HTTP + WS)
# ——————————————————————————————
application = ProtocolTypeRouter({
    # Peticiones HTTP “normales”
    "http": get_asgi_application(),

    # WebSocket: envuelto en AuthMiddlewareStack
    "websocket": AuthMiddlewareStack(
        URLRouter(websocket_urlpatterns)
    ),
})

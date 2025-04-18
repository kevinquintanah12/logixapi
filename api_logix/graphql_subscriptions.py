# api_logix/consumers.py
import channels_graphql_ws
from entrega.schema import schema   # tu schema de GraphQL
from rutas.schema import schema   # tu schema de GraphQL

class MyGraphqlWsConsumer(channels_graphql_ws.GraphqlWsConsumer):
    schema = schema

    async def on_connect(self, payload):
        # aquí puedes validar el token JWT si quieres
        return

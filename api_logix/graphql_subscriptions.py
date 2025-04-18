import channels_graphql_ws

from entrega.schema import schema  # tu schema de GraphQL

class MyGraphqlWsConsumer(channels_graphql_ws.GraphqlWsConsumer):
    schema = schema

    async def on_connect(self, payload):
        # Puedes hacer lógica de autenticación aquí
        pass

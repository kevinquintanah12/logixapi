# api_logix/consumers.py
import channels_graphql_ws
from entrega.schema import schema as entrega_schema
from rutas.schema import schema as rutas_schema
from sensoresRuta.schema import schema as sensores_schema
class MyGraphqlWsConsumer(channels_graphql_ws.GraphqlWsConsumer):
    schema = entrega_schema  # Puedes fusionar los dos si quieres más adelante
    schema = rutas_schema # Puedes fusionar los dos si quieres más adelante
    schema = sensores_schema

    async def on_connect(self, payload):
        return

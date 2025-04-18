from django.urls import path
from entrega.graphql_subscriptions import MyGraphqlWsConsumer

websocket_urlpatterns = [
    path("graphql/", MyGraphqlWsConsumer.as_asgi()),
]

# api_logix/routing.py
from django.urls import re_path
from api_logix.consumer import MyGraphqlWsConsumer

websocket_urlpatterns = [
    # monta el consumer en ws://<host>/graphql/
    re_path(r"^graphql/?$", MyGraphqlWsConsumer),
]

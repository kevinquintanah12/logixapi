# schema.py

import graphene
from graphene_django import DjangoObjectType
from django.db.models import Q
from .models import Destinatario

# ---------------------------------------------------
# Tipo GraphQL para Destinatario
# ---------------------------------------------------
class DestinatarioType(DjangoObjectType):
    class Meta:
        model = Destinatario
        fields = "__all__"


# ---------------------------------------------------
# Query: obtener individual, todos, último y búsqueda parcial
# ---------------------------------------------------
class Query(graphene.ObjectType):
    destinatario                 = graphene.Field(DestinatarioType, id=graphene.Int(required=True))
    todos_los_destinatarios      = graphene.List(DestinatarioType)
    ultimo_destinatario          = graphene.Field(DestinatarioType)
    buscar_destinatarios         = graphene.List(
        DestinatarioType,
        termino=graphene.String(required=True),
    )

    def resolve_destinatario(self, info, id):
        return Destinatario.objects.get(id=id)

    def resolve_todos_los_destinatarios(self, info):
        return Destinatario.objects.all()

    def resolve_ultimo_destinatario(self, info):
        return Destinatario.objects.order_by("-id").first()

    def resolve_buscar_destinatarios(self, info, termino):
        return Destinatario.objects.filter(
            Q(rfc__icontains=termino) |
            Q(nombre__icontains=termino) |
            Q(apellidos__icontains=termino) |
            Q(correo_electronico__icontains=termino) |
            Q(telefono__icontains=termino) |
            Q(direccion_detallada__icontains=termino) |
            Q(calle__icontains=termino) |
            Q(colonia__icontains=termino) |
            Q(numero__icontains=termino) |
            Q(ciudad__icontains=termino) |
            Q(estado__icontains=termino) |
            Q(codigo_postal__icontains=termino)
        ).distinct()


# ---------------------------------------------------
# Mutación para crear un destinatario
# ---------------------------------------------------
class CrearDestinatario(graphene.Mutation):
    class Arguments:
        rfc               = graphene.String()
        nombre            = graphene.String(required=True)
        apellidos         = graphene.String(required=True)
        correo_electronico= graphene.String()
        telefono          = graphene.String()
        direccion_detallada = graphene.String(required=True)
        calle             = graphene.String(required=True)
        colonia           = graphene.String(required=True)
        numero            = graphene.String(required=True)
        ciudad            = graphene.String(required=True)
        estado            = graphene.String(required=True)
        codigo_postal     = graphene.String(required=True)

    destinatario = graphene.Field(DestinatarioType)

    def mutate(self, info, **kwargs):
        destinatario = Destinatario(**kwargs)
        destinatario.obtener_coordenadas()  # Obtiene y asigna lat/lng antes de guardar
        destinatario.save()
        return CrearDestinatario(destinatario=destinatario)


# ---------------------------------------------------
# Agrupamos las mutaciones
# ---------------------------------------------------
class Mutation(graphene.ObjectType):
    crear_destinatario = CrearDestinatario.Field()


# ---------------------------------------------------
# Esquema final
# ---------------------------------------------------
schema = graphene.Schema(
    query=Query,
    mutation=Mutation,
)

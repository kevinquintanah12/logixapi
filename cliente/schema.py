# schema.py

import graphene
from graphene_django import DjangoObjectType
from django.db.models import Q
from .models import Cliente

# ---------------------------------------------------
# 1) Tipo GraphQL para Cliente
# ---------------------------------------------------
class ClienteType(DjangoObjectType):
    class Meta:
        model = Cliente
        fields = "__all__"


# ---------------------------------------------------
# 2) Query: individual, listado, último y búsqueda parcial
# ---------------------------------------------------
class Query(graphene.ObjectType):
    cliente              = graphene.Field(ClienteType, id=graphene.Int(required=True))
    ultimo_cliente       = graphene.Field(ClienteType)
    clientes             = graphene.List(ClienteType)
    buscar_clientes      = graphene.List(
        ClienteType,
        termino=graphene.String(required=True),
    )

    def resolve_cliente(self, info, id):
        return Cliente.objects.get(id=id)

    def resolve_ultimo_cliente(self, info):
        return Cliente.objects.order_by("-id").first()

    def resolve_clientes(self, info):
        return Cliente.objects.all()

    def resolve_buscar_clientes(self, info, termino):
        # Busca en varios campos aunque sea fragmento
        return Cliente.objects.filter(
            Q(nombre__icontains=termino) |
            Q(apellido__icontains=termino) |
            Q(razon_social__icontains=termino) |
            Q(rfc__icontains=termino) |
            Q(direccion__icontains=termino) |
            Q(codigo_postal__icontains=termino) |
            Q(telefono__icontains=termino) |
            Q(email__icontains=termino)
        ).distinct()


# ---------------------------------------------------
# 3) Mutaciones para Cliente
# ---------------------------------------------------
class CrearCliente(graphene.Mutation):
    class Arguments:
        nombre        = graphene.String(required=True)
        apellido      = graphene.String(required=True)
        razon_social  = graphene.String()
        rfc           = graphene.String(required=True)
        direccion     = graphene.String(required=True)
        codigo_postal = graphene.String(required=True)
        telefono      = graphene.String()
        email         = graphene.String()

    cliente = graphene.Field(ClienteType)

    def mutate(self, info, nombre, apellido, razon_social, rfc, direccion, codigo_postal, telefono=None, email=None):
        cliente = Cliente.objects.create(
            nombre=nombre,
            apellido=apellido,
            razon_social=razon_social,
            rfc=rfc,
            direccion=direccion,
            codigo_postal=codigo_postal,
            telefono=telefono,
            email=email
        )
        return CrearCliente(cliente=cliente)


class ActualizarCliente(graphene.Mutation):
    class Arguments:
        id            = graphene.Int(required=True)
        nombre        = graphene.String()
        apellido      = graphene.String()
        razon_social  = graphene.String()
        rfc           = graphene.String()
        direccion     = graphene.String()
        codigo_postal = graphene.String()
        telefono      = graphene.String()
        email         = graphene.String()

    cliente = graphene.Field(ClienteType)

    def mutate(self, info, id, **kwargs):
        cliente = Cliente.objects.get(id=id)
        for attr, value in kwargs.items():
            if value is not None:
                setattr(cliente, attr, value)
        cliente.save()
        return ActualizarCliente(cliente=cliente)


class EliminarCliente(graphene.Mutation):
    class Arguments:
        id = graphene.Int(required=True)

    ok = graphene.Boolean()

    def mutate(self, info, id):
        try:
            cliente = Cliente.objects.get(id=id)
            cliente.delete()
            return EliminarCliente(ok=True)
        except Cliente.DoesNotExist:
            return EliminarCliente(ok=False)


class Mutation(graphene.ObjectType):
    crear_cliente      = CrearCliente.Field()
    actualizar_cliente = ActualizarCliente.Field()
    eliminar_cliente   = EliminarCliente.Field()


# ---------------------------------------------------
# 4) Schema final
# ---------------------------------------------------
schema = graphene.Schema(
    query=Query,
    mutation=Mutation,
)

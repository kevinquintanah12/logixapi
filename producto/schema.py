import graphene
from graphene_django.types import DjangoObjectType
from .models import Producto
from destinatario.models import Destinatario
from cliente.models import Cliente
from calcularenvio.models import CalcularEnvio

# Definir el tipo de GraphQL para el modelo Producto
class ProductoType(DjangoObjectType):
    class Meta:
        model = Producto
        fields = "__all__"  # O puedes especificar los campos que deseas exponer

# Definir la mutación para crear un producto
class CrearProducto(graphene.Mutation):
    class Arguments:
        description = graphene.String(required=True)
        codigosat = graphene.String(required=True)
        noidentificacion = graphene.String(required=True)
        codigobarras = graphene.String()  # Este es opcional, ya que puede ser null
        destinatario_id = graphene.Int(required=True)
        cliente_id = graphene.Int(required=True)
        calculoenvio_id = graphene.Int(required=True)

    producto = graphene.Field(ProductoType)

    def mutate(self, info, description, codigosat, noidentificacion, codigobarras, destinatario_id, cliente_id, calculoenvio_id):
        # Obtener las instancias relacionadas por sus IDs
        destinatario = Destinatario.objects.get(id=destinatario_id)
        cliente = Cliente.objects.get(id=cliente_id)
        calculoenvio = CalcularEnvio.objects.get(id=calculoenvio_id)

        # Crear el nuevo producto
        producto = Producto.objects.create(
            description=description,
            codigosat=codigosat,
            noidentificacion=noidentificacion,
            codigobarras=codigobarras,
            destinatario=destinatario,
            cliente=cliente,
            calculoenvio=calculoenvio
        )

        return CrearProducto(producto=producto)

# Definir las consultas disponibles en GraphQL
class Query(graphene.ObjectType):
    producto = graphene.Field(ProductoType, id=graphene.Int(required=True))

    def resolve_producto(self, info, id):
        return Producto.objects.get(id=id)

# Definir las mutaciones disponibles en GraphQL
class Mutation(graphene.ObjectType):
    crear_producto = CrearProducto.Field()

# Definir el esquema de GraphQL
schema = graphene.Schema(query=Query, mutation=Mutation)

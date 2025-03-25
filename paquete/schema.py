import graphene
from graphene_django.types import DjangoObjectType
from .models import Paquete
from producto.models import Producto  # Importa el modelo Producto

# Definimos el tipo GraphQL para el modelo Paquete
class PaqueteType(DjangoObjectType):
    class Meta:
        model = Paquete
        fields = "__all__"

# Mutación para crear un paquete
class CrearPaquete(graphene.Mutation):
    class Arguments:
        producto_id = graphene.Int(required=True)  # Solo necesitas el id del producto

    paquete = graphene.Field(PaqueteType)  # Devuelve el paquete creado

    def mutate(self, info, producto_id):
        # Obtener el producto relacionado por el ID proporcionado
        producto = Producto.objects.get(id=producto_id)

        # Crear el paquete con el producto relacionado
        paquete = Paquete.objects.create(producto=producto)

        return CrearPaquete(paquete=paquete)


# Query para obtener un paquete por ID
class Query(graphene.ObjectType):
    paquete = graphene.Field(PaqueteType, id=graphene.Int(required=True))  # Query para obtener un paquete

    def resolve_paquete(self, info, id):
        # Obtener el paquete por ID
        return Paquete.objects.get(id=id)


# Mutaciones disponibles
class Mutation(graphene.ObjectType):
    crear_paquete = CrearPaquete.Field()  # La mutación de creación de paquete

# Esquema final
schema = graphene.Schema(query=Query, mutation=Mutation)

import graphene
from graphene_django import DjangoObjectType
from .models import Cliente

# Definición del tipo Cliente para GraphQL
class ClienteType(DjangoObjectType):
    class Meta:
        model = Cliente
        fields = "__all__"  # Puedes especificar los campos que quieres exponer aquí

# Consultas para Cliente
class Query(graphene.ObjectType):
    cliente = graphene.Field(ClienteType, id=graphene.Int(required=True))
    ultimo_cliente = graphene.Field(ClienteType)

    def resolve_cliente(self, info, id):
        return Cliente.objects.get(id=id)
    
    def resolve_ultimo_cliente(self, info):
        return Cliente.objects.order_by('-id').first()

# Mutaciones para Cliente
class CrearCliente(graphene.Mutation):
    class Arguments:
        nombre = graphene.String(required=True)
        apellido = graphene.String(required=True)
        razon_social = graphene.String()
        rfc = graphene.String(required=True)
        direccion = graphene.String(required=True)
        codigo_postal = graphene.String(required=True)
        telefono = graphene.String()
        email = graphene.String()

    cliente = graphene.Field(ClienteType)

    def mutate(self, info, nombre, apellido, razon_social, rfc, direccion, codigo_postal, telefono, email):
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

# Esquema de Mutaciones
class Mutation(graphene.ObjectType):
    crear_cliente = CrearCliente.Field()

# Esquema completo de Cliente
schema = graphene.Schema(query=Query, mutation=Mutation)

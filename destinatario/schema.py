import graphene
from graphene_django import DjangoObjectType
from .models import Destinatario

# Tipo GraphQL para Destinatario
class DestinatarioType(DjangoObjectType):
    class Meta:
        model = Destinatario
        fields = "__all__"

# Query para obtener destinatarios
class Query(graphene.ObjectType):
    destinatario = graphene.Field(DestinatarioType, id=graphene.Int(required=True))
    todos_los_destinatarios = graphene.List(DestinatarioType)
    ultimo_destinatario = graphene.Field(DestinatarioType)

    def resolve_destinatario(self, info, id):
        return Destinatario.objects.get(id=id)

    def resolve_todos_los_destinatarios(self, info):
        return Destinatario.objects.all()

    def resolve_ultimo_destinatario(self, info):
        return Destinatario.objects.order_by('-id').first()

# Mutación para crear un destinatario
class CrearDestinatario(graphene.Mutation):
    class Arguments:
        rfc = graphene.String(required=False)
        nombre = graphene.String(required=True)
        apellidos = graphene.String(required=True)
        correo_electronico = graphene.String()
        telefono = graphene.String()
        pin = graphene.String()
        direccion_detallada = graphene.String(required=True)
        calle = graphene.String(required=True)
        colonia = graphene.String(required=True)
        numero = graphene.String(required=True)
        ciudad = graphene.String(required=True)
        estado = graphene.String(required=True)
        codigo_postal = graphene.String(required=True)

    destinatario = graphene.Field(DestinatarioType)

    def mutate(self, info, **kwargs):
        destinatario = Destinatario(**kwargs)
        destinatario.obtener_coordenadas()  # Obtiene las coordenadas antes de guardar
        destinatario.save()
        return CrearDestinatario(destinatario=destinatario)

# Esquema de Mutaciones
class Mutation(graphene.ObjectType):
    crear_destinatario = CrearDestinatario.Field()

# Esquema completo
schema = graphene.Schema(query=Query, mutation=Mutation)

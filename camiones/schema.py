import graphene
from graphene_django.types import DjangoObjectType
from .models import Camion

# Tipo GraphQL para Camion
class CamionType(DjangoObjectType):
    class Meta:
        model = Camion
        fields = "__all__"

# Query para obtener un camion por ID
class Query(graphene.ObjectType):
    camion = graphene.Field(CamionType, id=graphene.Int(required=True))

    def resolve_camion(self, info, id):
        # Obtener el camion por ID
        return Camion.objects.get(id=id)

# Mutación para crear un camion
class CrearCamion(graphene.Mutation):
    class Arguments:
        matricula = graphene.String(required=True)
        marca = graphene.String(required=True)
        modelo = graphene.String(required=True)
        capacidad_carga = graphene.Float(required=True)
        tipo_vehiculo = graphene.String(required=True)
        cumplimiento_normas = graphene.Boolean(required=True)

    camion = graphene.Field(CamionType)

    def mutate(self, info, matricula, marca, modelo, capacidad_carga, tipo_vehiculo, cumplimiento_normas):
        # Crear el camion
        camion = Camion.objects.create(
            matricula=matricula,
            marca=marca,
            modelo=modelo,
            capacidad_carga=capacidad_carga,
            tipo_vehiculo=tipo_vehiculo,
            cumplimiento_normas=cumplimiento_normas
        )

        return CrearCamion(camion=camion)

# Mutaciones disponibles
class Mutation(graphene.ObjectType):
    crear_camion = CrearCamion.Field()  # Mutación para crear un camion

# Esquema final
schema = graphene.Schema(query=Query, mutation=Mutation)

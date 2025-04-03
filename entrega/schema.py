import graphene
from graphene_django.types import DjangoObjectType
from .models import Entrega
from destinatario.models import Destinatario
from centrodistribucion.models import CentroDistribucion
from paquete.models import Paquete

# Tipo GraphQL para Entrega
class EntregaType(DjangoObjectType):
    class Meta:
        model = Entrega
        fields = "__all__"

# Mutación para crear una entrega sin ruta asignada
class CrearEntrega(graphene.Mutation):
    class Arguments:
        paquete_id = graphene.Int(required=True)
        fecha_entrega = graphene.DateTime(required=True)
        estado = graphene.String(required=True)
        pin = graphene.String(required=True)

    entrega = graphene.Field(EntregaType)

    def mutate(self, info, paquete_id, fecha_entrega, estado, pin):
        paquete = Paquete.objects.get(id=paquete_id)

        # Crear la entrega sin asignar ruta (ruta queda null)
        entrega = Entrega.objects.create(
            paquete=paquete,
            fecha_entrega=fecha_entrega,
            estado=estado,
            pin=pin,
        )
        return CrearEntrega(entrega=entrega)

# Mutación para actualizar el estado de una entrega
class ActualizarEstadoEntrega(graphene.Mutation):
    class Arguments:
        entrega_id = graphene.Int(required=True)
        estado = graphene.String(required=True)

    entrega = graphene.Field(EntregaType)

    def mutate(self, info, entrega_id, estado):
        entrega = Entrega.objects.get(id=entrega_id)
        entrega.estado = estado
        entrega.save()
        return ActualizarEstadoEntrega(entrega=entrega)

# Queries para obtener entregas
class Query(graphene.ObjectType):
    entrega = graphene.Field(EntregaType, id=graphene.Int(required=True))
    entrega_por_guia = graphene.Field(EntregaType, numero_guia=graphene.String(required=True))
    entregas_por_estado = graphene.List(EntregaType, estado=graphene.String(required=True))
    entregas_por_paquete = graphene.List(EntregaType, paquete_id=graphene.Int(required=True))
    entregas_por_fecha = graphene.List(EntregaType, fecha_entrega=graphene.DateTime(required=True))
    entregas_por_ciudad_estado = graphene.List(
        EntregaType, ciudad=graphene.String(required=True), estado=graphene.String(required=True)
    )

    def resolve_entrega(self, info, id):
        return Entrega.objects.get(id=id)

    def resolve_entrega_por_guia(self, info, numero_guia):
        return Entrega.objects.get(paquete__numero_guia=numero_guia)

    def resolve_entregas_por_estado(self, info, estado):
        return Entrega.objects.filter(estado=estado)

    def resolve_entregas_por_paquete(self, info, paquete_id):
        return Entrega.objects.filter(paquete_id=paquete_id)

    def resolve_entregas_por_fecha(self, info, fecha_entrega):
        return Entrega.objects.filter(fecha_entrega=fecha_entrega)

    def resolve_entregas_por_ciudad_estado(self, info, ciudad, estado):
        return Entrega.objects.filter(destinatario__ciudad=ciudad, destinatario__estado=estado)

# Mutaciones disponibles en el esquema de Entregas
class Mutation(graphene.ObjectType):
    crear_entrega = CrearEntrega.Field()
    actualizar_estado_entrega = ActualizarEstadoEntrega.Field()

# Esquema GraphQL
schema = graphene.Schema(query=Query, mutation=Mutation)

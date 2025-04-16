import graphene
from graphene_django.types import DjangoObjectType
from .models import Entrega
from paquete.models import Paquete
#from django.contrib.auth import get_user_model
#
# Si en algún momento necesitas el usuario, ya no se usará para asignar el chofer.
# User = get_user_model()

# Tipo GraphQL para Entrega
class EntregaType(DjangoObjectType):
    class Meta:
        model = Entrega
        fields = "__all__"

# Mutación para crear una entrega sin asignar chofer
class CrearEntrega(graphene.Mutation):
    class Arguments:
        paquete_id = graphene.Int(required=True)
        fecha_entrega = graphene.DateTime(required=True)
        estado = graphene.String(required=True)
        pin = graphene.String(required=True)

    entrega = graphene.Field(EntregaType)

    def mutate(self, info, paquete_id, fecha_entrega, estado, pin):
        paquete = Paquete.objects.get(id=paquete_id)
        # Se crea la entrega sin asignar chofer
        entrega = Entrega.objects.create(
            paquete=paquete,
            fecha_entrega=fecha_entrega,
            estado=estado,
            pin=pin,
        )
        return CrearEntrega(entrega=entrega)

# Mutación para finalizar la entrega validando el PIN y actualizando el estado
class FinalizarEntrega(graphene.Mutation):
    class Arguments:
        entrega_id = graphene.Int(required=True)
        pin = graphene.String(required=True)
        estado = graphene.String(required=True)

    entrega = graphene.Field(EntregaType)
    error = graphene.String()

    def mutate(self, info, entrega_id, pin, estado):
        entrega = Entrega.objects.get(id=entrega_id)
        
        if entrega.pin != pin:
            return FinalizarEntrega(error="PIN incorrecto")

        entrega.estado = estado
        entrega.save()

        return FinalizarEntrega(entrega=entrega)

# Mutación para eliminar TODAS las entregas
class EliminarTodasEntregas(graphene.Mutation):
    success = graphene.Boolean()

    def mutate(self, info):
        # Se eliminan todas las entregas de la base de datos
        _, _ = Entrega.objects.all().delete()
        return EliminarTodasEntregas(success=True)

# Mutación para eliminar una entrega por ID
class EliminarEntregaPorId(graphene.Mutation):
    class Arguments:
        id = graphene.Int(required=True)

    success = graphene.Boolean()
    error = graphene.String()

    def mutate(self, info, id):
        try:
            entrega = Entrega.objects.get(id=id)
            entrega.delete()
            return EliminarEntregaPorId(success=True)
        except Entrega.DoesNotExist:
            return EliminarEntregaPorId(success=False, error="Entrega no encontrada")

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
    mis_entregas_en_proceso = graphene.List(EntregaType)

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

    def resolve_mis_entregas_en_proceso(self, info):
        # Se eliminó el filtro por chofer, ya que el campo no existe.
        return Entrega.objects.filter(estado="En proceso")

# Mutaciones disponibles en el esquema de Entregas
class Mutation(graphene.ObjectType):
    crear_entrega = CrearEntrega.Field()
    finalizar_entrega = FinalizarEntrega.Field()
    eliminar_todas_entregas = EliminarTodasEntregas.Field()
    eliminar_entrega_por_id = EliminarEntregaPorId.Field()

# Esquema GraphQL
schema = graphene.Schema(query=Query, mutation=Mutation)

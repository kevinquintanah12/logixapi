import graphene
from graphene_django.types import DjangoObjectType
from .models import Ruta
from chofer.models import Chofer
from camiones.models import Camion
from entrega.models import Entrega
from paquete.models import Paquete  # Importamos Paquete

# Tipo GraphQL para Ruta
class RutaType(DjangoObjectType):
    class Meta:
        model = Ruta
        fields = "__all__"

# Mutación para crear una ruta
class CrearRuta(graphene.Mutation):
    class Arguments:
        distancia = graphene.Float(required=True)
        prioridad = graphene.Int(required=True)
        conductor_id = graphene.Int(required=True)
        vehiculo_id = graphene.Int(required=True)
        fecha_inicio = graphene.DateTime(required=True)
        fecha_fin = graphene.DateTime(required=True)
        estado = graphene.String(required=False, default_value="por hacer")
        entrega_id = graphene.Int(required=True)

    ruta = graphene.Field(RutaType)

    def mutate(self, info, distancia, prioridad, conductor_id, vehiculo_id, fecha_inicio, fecha_fin, estado, entrega_id):
        vehiculo = Camion.objects.get(id=vehiculo_id)
        conductor = Chofer.objects.get(id=conductor_id)
        entrega = Entrega.objects.get(id=entrega_id)

        ruta = Ruta.objects.create(
            distancia=distancia,
            prioridad=prioridad,
            conductor=conductor,
            vehiculo=vehiculo,
            fecha_inicio=fecha_inicio,
            fecha_fin=fecha_fin,
            estado=estado
        )

        # Relacionar la entrega con la ruta (si la relación es ManyToMany)
        ruta.entregas.add(entrega)

        return CrearRuta(ruta=ruta)

# Queries para obtener rutas
class Query(graphene.ObjectType):
    ruta = graphene.Field(RutaType, id=graphene.Int(required=True))
    mis_rutas = graphene.List(RutaType)
    rutas_por_estado = graphene.List(RutaType, estado=graphene.String(required=True))
    ruta_por_guia = graphene.Field(RutaType, numero_guia=graphene.String(required=True))  # Nueva consulta

    def resolve_ruta(self, info, id):
        return Ruta.objects.get(id=id)

    def resolve_mis_rutas(self, info):
        user = info.context.user
        conductor = Chofer.objects.get(usuario=user)
        return Ruta.objects.filter(conductor=conductor)

    def resolve_rutas_por_estado(self, info, estado):
        return Ruta.objects.filter(estado=estado)

    def resolve_ruta_por_guia(self, info, numero_guia):
        try:
            return Ruta.objects.get(entregas__paquete__numero_guia=numero_guia)
        except Ruta.DoesNotExist:
            return None

# Mutaciones disponibles en el esquema de Rutas
class Mutation(graphene.ObjectType):
    crear_ruta = CrearRuta.Field()

# Esquema GraphQL
schema = graphene.Schema(query=Query, mutation=Mutation)

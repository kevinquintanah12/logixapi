import graphene
from graphene_django.types import DjangoObjectType
from .models import Ruta
from chofer.models import Chofer
from camiones.models import Camion
from entrega.models import Entrega
from paquete.models import Paquete  # Importamos Paquete

# Importamos la función que envía notificaciones
from fcm.firebase_config import enviar_notificacion_fcm_v1
from fcm.models import FCMDevice  # Modelo donde se guarda el token FCM

# Tipo GraphQL para Ruta
class RutaType(DjangoObjectType):
    class Meta:
        model = Ruta
        fields = "__all__"

# Mutación para crear una ruta y notificar al chofer
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
        # Obtener instancias de los modelos relacionados
        vehiculo = Camion.objects.get(id=vehiculo_id)
        conductor = Chofer.objects.get(id=conductor_id)
        entrega = Entrega.objects.get(id=entrega_id)

        # Crear la ruta
        ruta = Ruta.objects.create(
            distancia=distancia,
            prioridad=prioridad,
            conductor=conductor,
            vehiculo=vehiculo,
            fecha_inicio=fecha_inicio,
            fecha_fin=fecha_fin,
            estado=estado
        )

        # Asociar la entrega a la ruta
        ruta.entregas.add(entrega)

        # Intentar enviar la notificación push al chofer asignado
        try:
            # Buscamos el token FCM registrado para el usuario (chofer)
            fcm_device = FCMDevice.objects.get(user=conductor.usuario)
            enviar_notificacion_fcm_v1(
                token=fcm_device.token,
                title="Nueva Ruta Asignada",
                body="Se te ha asignado una nueva ruta."
            )
        except FCMDevice.DoesNotExist:
            print("El chofer no tiene token FCM registrado.")

        return CrearRuta(ruta=ruta)

# Queries para obtener rutas
class Query(graphene.ObjectType):
    ruta = graphene.Field(RutaType, id=graphene.Int(required=True))
    mis_rutas = graphene.List(RutaType)
    rutas_por_estado = graphene.List(RutaType, estado=graphene.String(required=True))
    ruta_por_guia = graphene.Field(RutaType, numero_guia=graphene.String(required=True))  # Consultar por número de guía

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

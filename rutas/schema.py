import graphene
from graphene_django.types import DjangoObjectType

# Importamos los modelos
from .models import Ruta
from chofer.models import Chofer
from camiones.models import Camion
from entrega.models import Entrega
from paquete.models import Paquete

# Importamos la función para notificaciones push
from fcm.firebase_config import enviar_notificacion_fcm_v1
from fcm.models import FCMDevice

# Tipo GraphQL para el modelo Paquete
class PaqueteType(DjangoObjectType):
    class Meta:
        model = Paquete
        fields = "__all__"

# Tipo GraphQL para el modelo Entrega
class EntregaType(DjangoObjectType):
    class Meta:
        model = Entrega
        fields = "__all__"

# Tipo GraphQL para el modelo Camion
class CamionType(DjangoObjectType):
    class Meta:
        model = Camion
        fields = "__all__"

# Tipo GraphQL para el modelo Chofer
class ChoferType(DjangoObjectType):
    class Meta:
        model = Chofer
        fields = "__all__"

# Tipo GraphQL para el modelo Ruta (incluye todas las relaciones)
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

    def mutate(
        self, info, distancia, prioridad, conductor_id, vehiculo_id,
        fecha_inicio, fecha_fin, estado, entrega_id
    ):
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

# Mutación para cambiar el estado de una ruta existente
class CambiarEstadoRuta(graphene.Mutation):
    class Arguments:
        ruta_id = graphene.Int(required=True)
        nuevo_estado = graphene.String(required=True)

    ruta = graphene.Field(RutaType)

    def mutate(self, info, ruta_id, nuevo_estado):
        try:
            ruta = Ruta.objects.get(id=ruta_id)
            ruta.estado = nuevo_estado
            ruta.save()

            # Ejemplo: Enviar notificación al chofer cuando se actualiza el estado
            try:
                conductor = ruta.conductor
                fcm_device = FCMDevice.objects.get(user=conductor.usuario)
                enviar_notificacion_fcm_v1(
                    token=fcm_device.token,
                    title="Estado Actualizado",
                    body=f"La ruta {ruta_id} ha cambiado a: {nuevo_estado}."
                )
            except FCMDevice.DoesNotExist:
                print("El chofer no tiene token FCM registrado.")

            return CambiarEstadoRuta(ruta=ruta)
        except Ruta.DoesNotExist:
            raise Exception("Ruta no encontrada")

# Definición de las consultas (queries)
class Query(graphene.ObjectType):
    # Consulta para obtener una ruta por ID
    ruta = graphene.Field(RutaType, id=graphene.Int(required=True))
    # Consulta para obtener rutas asociadas al chofer conectado
    mis_rutas = graphene.List(RutaType)
    # Consulta para obtener rutas filtradas por estado
    rutas_por_estado = graphene.List(RutaType, estado=graphene.String(required=True))
    # Consulta para obtener una ruta buscando por número de guía
    ruta_por_guia = graphene.Field(RutaType, numero_guia=graphene.String(required=True))
    # Consulta que devuelve todas las rutas (con todas sus relaciones) filtradas por estado
    rutas_completas_por_estado = graphene.List(RutaType, estado=graphene.String(required=True))

    def resolve_ruta(self, info, id):
        return Ruta.objects.get(id=id)

    def resolve_mis_rutas(self, info):
        # Se asume que info.context.user es el usuario autenticado
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

    def resolve_rutas_completas_por_estado(self, info, estado):
        # Retorna todas las rutas filtradas por estado, incluyendo todos los datos anidados (chofer, camión, entregas y paquetes).
        return Ruta.objects.filter(estado=estado)

# Agrupamos las mutaciones disponibles
class Mutation(graphene.ObjectType):
    crear_ruta = CrearRuta.Field()
    cambiar_estado_ruta = CambiarEstadoRuta.Field()

# Esquema GraphQL completo
schema = graphene.Schema(query=Query, mutation=Mutation)

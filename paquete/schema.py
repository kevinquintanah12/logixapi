import graphene
from graphene_django.types import DjangoObjectType
from email.mime.text import MIMEText
import smtplib
import datetime

from .models import Paquete
from producto.models import Producto  # Asegúrate de que esté importado correctamente

# Tipo GraphQL para el modelo Paquete, con un campo calculado para la fecha estimada de entrega
class PaqueteType(DjangoObjectType):
    fecha_estimada_entrega = graphene.DateTime()

    class Meta:
        model = Paquete
        fields = "__all__"

    def resolve_fecha_estimada_entrega(self, info):
        # Usamos "fecha_registro" como fecha de creación
        created = self.fecha_registro
        # Se accede al cálculo de envío a través del producto relacionado.
        # Se espera que self.producto.calculoenvio tenga los campos "envioExpress" y "distanciaKm"
        envio_express = self.producto.calculoenvio.envioExpress
        distancia = float(self.producto.calculoenvio.distanciaKm)
        # Si es envío express se entrega el mismo día; de lo contrario, se entrega al siguiente día.
        # Opcionalmente, podrías usar la distancia para algún cálculo adicional.
        if envio_express:
            return created
        else:
            return created + datetime.timedelta(days=1)

# Mutación para crear un paquete a partir de un producto
class CrearPaquete(graphene.Mutation):
    class Arguments:
        producto_id = graphene.Int(required=True)  # Se requiere el ID del producto

    paquete = graphene.Field(PaqueteType)

    def mutate(self, info, producto_id):
        # Obtener el producto relacionado por su ID
        producto = Producto.objects.get(id=producto_id)
        # Crear el paquete con el producto relacionado; se asume que al crearse se asigna un número de guía automáticamente
        paquete = Paquete.objects.create(producto=producto)
        return CrearPaquete(paquete=paquete)

# Mutación para enviar el número de guía (generado en Paquete) a dos correos electrónicos
class EnviarGuiaEmail(graphene.Mutation):
    class Arguments:
        paquete_id = graphene.Int(required=True)
        email1 = graphene.String(required=True)
        email2 = graphene.String(required=True)

    success = graphene.Boolean()
    paquete = graphene.Field(PaqueteType)

    def mutate(self, info, paquete_id, email1, email2):
        try:
            # Obtener el paquete por su ID
            paquete = Paquete.objects.get(id=paquete_id)
        except Paquete.DoesNotExist:
            raise Exception("Paquete no encontrado")

        # Obtener el número de guía del paquete
        numero_guia = paquete.numero_guia

        # Configurar el asunto y cuerpo del correo
        subject = "Número de Guía de su Paquete"
        body = (
            f"Estimado cliente,\n\n"
            f"El número de guía de su paquete es: {numero_guia}\n\n"
            f"Gracias por su preferencia."
        )

        # Configuración del remitente y credenciales SMTP (actualiza estos datos según tu entorno)
        sender_email = "logisticlogix0@gmail.com"  # Correo de envío
        app_password = "nzvi ailf xxck gctf" 

        # Crear el mensaje de correo en formato texto
        message = MIMEText(body, "plain")
        message["Subject"] = subject
        message["From"] = sender_email

        # Lista de destinatarios
        recipients = [email1, email2]

        try:
            # Enviar el correo utilizando SMTP con SSL (en este caso, Gmail)
            with smtplib.SMTP_SSL("smtp.gmail.com", 465) as server:
                server.login(sender_email, app_password)
                server.sendmail(sender_email, recipients, message.as_string())
            success = True
        except Exception as e:
            print(f"Error al enviar el correo: {e}")
            success = False

        return EnviarGuiaEmail(success=success, paquete=paquete)

# Query para obtener paquetes
class Query(graphene.ObjectType):
    paquete = graphene.Field(PaqueteType, id=graphene.Int(required=True))
    paquetes = graphene.List(PaqueteType)
    ultimo_paquete = graphene.Field(PaqueteType)

    def resolve_paquete(self, info, id):
        return Paquete.objects.get(id=id)

    def resolve_paquetes(self, info):
        return Paquete.objects.all()

    def resolve_ultimo_paquete(self, info):
        return Paquete.objects.last()

# Mutaciones disponibles
class Mutation(graphene.ObjectType):
    crear_paquete = CrearPaquete.Field()
    enviar_guia_email = EnviarGuiaEmail.Field()

# Esquema final
schema = graphene.Schema(query=Query, mutation=Mutation)

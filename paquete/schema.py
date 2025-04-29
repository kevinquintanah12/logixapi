import graphene
from graphene_django import DjangoObjectType
from .models import Paquete
from producto.models import Producto
from producto.schema import ProductoType
from email.mime.text import MIMEText
import smtplib

# ---------------------------------------------------
# 1) Tipo GraphQL para Producto (ya definido en producto/schema.py)
# ---------------------------------------------------
# from producto.schema import ProductoType

# ---------------------------------------------------
# 2) Tipo GraphQL para Paquete
#    - Exponemos explícitamente el campo `producto`
#    - Listamos sólo los campos que realmente usamos
# ---------------------------------------------------
class PaqueteType(DjangoObjectType):
    producto = graphene.Field(ProductoType)

    class Meta:
        model = Paquete
        fields = (
            "id",
            "numero_guia",
            "codigo_barras",
            "fecha_registro",
            "producto",
        )

    def resolve_producto(self, info):
        # Retornamos la instancia de Producto relacionada
        return self.producto

# ---------------------------------------------------
# 3) Mutación: crear un paquete a partir de un producto
# ---------------------------------------------------
class CrearPaquete(graphene.Mutation):
    class Arguments:
        producto_id = graphene.Int(required=True)

    paquete = graphene.Field(PaqueteType)

    def mutate(self, info, producto_id):
        producto = Producto.objects.get(id=producto_id)
        paquete = Paquete.objects.create(producto=producto)
        return CrearPaquete(paquete=paquete)

# ---------------------------------------------------
# 4) Mutación: enviar el número de guía por email
# ---------------------------------------------------
class EnviarGuiaEmail(graphene.Mutation):
    class Arguments:
        paquete_id = graphene.Int(required=True)
        email1     = graphene.String(required=True)
        email2     = graphene.String(required=True)

    success = graphene.Boolean()
    paquete = graphene.Field(PaqueteType)

    def mutate(self, info, paquete_id, email1, email2):
        paquete = Paquete.objects.get(id=paquete_id)
        numero_guia = paquete.numero_guia

        subject = "Número de Guía de su Paquete"
        body = (
            f"Estimado cliente,\n\n"
            f"El número de guía de su paquete es: {numero_guia}\n\n"
            "Gracias por su preferencia."
        )

        message = MIMEText(body, "plain")
        message["Subject"] = subject
        message["From"]    = "logisticlogix0@gmail.com"
        recipients = [email1, email2]

        try:
            with smtplib.SMTP_SSL("smtp.gmail.com", 465) as server:
                server.login("logisticlogix0@gmail.com", "tu_app_password")
                server.sendmail(message["From"], recipients, message.as_string())
            success = True
        except Exception as e:
            print(f"Error al enviar el correo: {e}")
            success = False

        return EnviarGuiaEmail(success=success, paquete=paquete)

# ---------------------------------------------------
# 5) Query: obtener paquetes
# ---------------------------------------------------
class Query(graphene.ObjectType):
    paquete          = graphene.Field(PaqueteType, id=graphene.Int(required=True))
    paquetes         = graphene.List(PaqueteType)
    ultimo_paquete   = graphene.Field(PaqueteType)

    def resolve_paquete(self, info, id):
        return Paquete.objects.get(id=id)

    def resolve_paquetes(self, info):
        return Paquete.objects.all()

    def resolve_ultimo_paquete(self, info):
        return Paquete.objects.last()

# ---------------------------------------------------
# 6) Agrupamos las mutaciones
# ---------------------------------------------------
class Mutation(graphene.ObjectType):
    crear_paquete    = CrearPaquete.Field()
    enviar_guia_email = EnviarGuiaEmail.Field()

# ---------------------------------------------------
# 7) Esquema final, registrando ProductoType
# ---------------------------------------------------
schema = graphene.Schema(
    query=Query,
    mutation=Mutation,
    types=[ProductoType],  # Para asegurar que Graphene incluya ProductoType
)

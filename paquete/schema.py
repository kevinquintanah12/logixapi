import graphene
from graphene_django import DjangoObjectType
from .models import Paquete
from producto.models import Producto
from producto.schema import ProductoType
from email.mime.text import MIMEText
import smtplib

# ---------------------------------------------------
# 1) Tipo GraphQL para Paquete
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
        return self.producto

# ---------------------------------------------------
# 2) Mutaciones existentes
#    - crear_paquete
#    - enviar_guia_email
# ---------------------------------------------------
class CrearPaquete(graphene.Mutation):
    class Arguments:
        producto_id = graphene.Int(required=True)

    paquete = graphene.Field(PaqueteType)

    def mutate(self, info, producto_id):
        producto = Producto.objects.get(id=producto_id)
        paquete = Paquete.objects.create(producto=producto)
        return CrearPaquete(paquete=paquete)

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
                server.login("logisticlogix0@gmail.com", "nzvi ailf xxck gctf")
                server.sendmail(message["From"], recipients, message.as_string())
            success = True
        except Exception as e:
            print(f"Error al enviar el correo: {e}")
            success = False

        return EnviarGuiaEmail(success=success, paquete=paquete)

# ---------------------------------------------------
# 3) Query: obtener y filtrar paquetes
# ---------------------------------------------------
class Query(graphene.ObjectType):
    paquete                  = graphene.Field(PaqueteType, id=graphene.Int(required=True))
    paquetes                 = graphene.List(PaqueteType)
    ultimo_paquete           = graphene.Field(PaqueteType)

    # Filtros
    paquetes_por_destinatario = graphene.List(
        PaqueteType, destinatario_id=graphene.Int(required=True)
    )
    paquetes_por_cliente      = graphene.List(
        PaqueteType, cliente_id=graphene.Int(required=True)
    )
    paquetes_por_nombre_destinatario = graphene.List(
        PaqueteType, nombre=graphene.String(required=True)
    )
    paquetes_por_nombre_cliente      = graphene.List(
        PaqueteType, nombre=graphene.String(required=True)
    )
    paquetes_por_numero_guia  = graphene.List(
        PaqueteType, numero_guia=graphene.String(required=True)
    )
    paquetes_por_codigo_barras = graphene.List(
        PaqueteType, codigo_barras=graphene.String(required=True)
    )

    def resolve_paquete(self, info, id):
        return Paquete.objects.get(id=id)

    def resolve_paquetes(self, info):
        return Paquete.objects.all()

    def resolve_ultimo_paquete(self, info):
        return Paquete.objects.last()

    def resolve_paquetes_por_destinatario(self, info, destinatario_id):
        return Paquete.objects.filter(producto__destinatario__id=destinatario_id)

    def resolve_paquetes_por_cliente(self, info, cliente_id):
        return Paquete.objects.filter(producto__cliente__id=cliente_id)

    def resolve_paquetes_por_nombre_destinatario(self, info, nombre):
        # Filtra por nombre del destinatario relacionado con el producto
        return Paquete.objects.filter(producto__destinatario__nombre__icontains=nombre)

    def resolve_paquetes_por_nombre_cliente(self, info, nombre):
        # Filtra por nombre del cliente relacionado con el producto
        return Paquete.objects.filter(producto__cliente__nombre__icontains=nombre)

    def resolve_paquetes_por_numero_guia(self, info, numero_guia):
        return Paquete.objects.filter(numero_guia__icontains=numero_guia)

    def resolve_paquetes_por_codigo_barras(self, info, codigo_barras):
        return Paquete.objects.filter(codigo_barras__icontains=codigo_barras)

# ---------------------------------------------------
# 4) Mutaciones al esquema
# ---------------------------------------------------
class Mutation(graphene.ObjectType):
    crear_paquete     = CrearPaquete.Field()
    enviar_guia_email = EnviarGuiaEmail.Field()

# ---------------------------------------------------
# 5) Schema final
# ---------------------------------------------------
schema = graphene.Schema(
    query=Query,
    mutation=Mutation,
    types=[ProductoType],
)

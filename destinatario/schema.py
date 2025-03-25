import graphene
from graphene_django import DjangoObjectType
from .models import Destinatario

# Definición del tipo Destinatario para GraphQL
class DestinatarioType(DjangoObjectType):
    class Meta:
        model = Destinatario
        fields = "__all__"  # Puedes especificar los campos que quieres exponer aquí

# Consultas para Destinatario
class Query(graphene.ObjectType):
    destinatario = graphene.Field(DestinatarioType, id=graphene.Int(required=True))

    def resolve_destinatario(self, info, id):
        return Destinatario.objects.get(id=id)

# Mutaciones para Destinatario
class CrearDestinatario(graphene.Mutation):
    class Arguments:
        rfc = graphene.String(required=True)
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

    def mutate(self, info, rfc, nombre, apellidos, correo_electronico, telefono, pin, direccion_detallada, calle, colonia, numero, ciudad, estado, codigo_postal):
        destinatario = Destinatario.objects.create(
            rfc=rfc,
            nombre=nombre,
            apellidos=apellidos,
            correo_electronico=correo_electronico,
            telefono=telefono,
            pin=pin,
            direccion_detallada=direccion_detallada,
            calle=calle,
            colonia=colonia,
            numero=numero,
            ciudad=ciudad,
            estado=estado,
            codigo_postal=codigo_postal
        )
        return CrearDestinatario(destinatario=destinatario)

# Esquema de Mutaciones
class Mutation(graphene.ObjectType):
    crear_destinatario = CrearDestinatario.Field()

# Esquema completo de Destinatario
schema = graphene.Schema(query=Query, mutation=Mutation)

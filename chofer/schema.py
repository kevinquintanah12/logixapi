import graphene
from graphene_django.types import DjangoObjectType
from .models import Chofer
from horarios.models import Horario
from horarios.schema import HorarioType
from django.contrib.auth.models import User

# Para el envío de correo
from email.mime.text import MIMEText
import smtplib

# Función para verificar si un PIN es secuencial
def es_secuencial(pin):
    ascending = all(int(pin[i]) + 1 == int(pin[i+1]) for i in range(len(pin) - 1))
    descending = all(int(pin[i]) - 1 == int(pin[i+1]) for i in range(len(pin) - 1))
    return ascending or descending

# Tipo GraphQL para el modelo Chofer
class ChoferType(DjangoObjectType):
    class Meta:
        model = Chofer

# Definición de consultas GraphQL
class Query(graphene.ObjectType):
    all_choferes = graphene.List(ChoferType)
    chofer_by_id = graphene.Field(ChoferType, id=graphene.Int())
    chofer_autenticado = graphene.Field(ChoferType)
    check_pin = graphene.Boolean(pin=graphene.String(required=True))

    def resolve_all_choferes(self, info, **kwargs):
        user = info.context.user
        if not user.is_authenticated:
            raise Exception("Debes estar autenticado para ver la lista de choferes.")
        return Chofer.objects.all()

    def resolve_chofer_by_id(self, info, id):
        user = info.context.user
        if not user.is_authenticated:
            raise Exception("Debes estar autenticado para ver los detalles de un chofer.")
        try:
            return Chofer.objects.get(pk=id)
        except Chofer.DoesNotExist:
            return None

    def resolve_chofer_autenticado(self, info):
        user = info.context.user
        if not user.is_authenticated:
            raise Exception("Debes estar autenticado para ver tu información.")
        try:
            return Chofer.objects.get(usuario=user)
        except Chofer.DoesNotExist:
            raise Exception("No tienes un chofer asociado a tu cuenta.")

    def resolve_check_pin(self, info, pin):
        user = info.context.user
        if not user.is_authenticated:
            raise Exception("Debes estar autenticado para verificar el PIN.")
        try:
            chofer = Chofer.objects.get(usuario=user)
        except Chofer.DoesNotExist:
            raise Exception("No se encontró un chofer asociado a tu cuenta.")
        return chofer.pin == pin

# Mutación para crear un Chofer recibiendo el userId y la contraseña en texto plano como argumentos
class CreateChofer(graphene.Mutation):
    class Arguments:
        user_id = graphene.Int(required=True)  # Recibe el ID del usuario
        nombre = graphene.String(required=True)
        apellidos = graphene.String(required=True)
        rfc = graphene.String(required=True)
        licencia = graphene.String(required=True)
        certificaciones = graphene.String()
        horario_id = graphene.Int(required=True)
        password = graphene.String(required=True)  # Contraseña en texto plano

    chofer = graphene.Field(ChoferType)

    def mutate(self, info, user_id, nombre, apellidos, rfc, licencia, certificaciones, horario_id, password):
        # Guardamos la contraseña en una variable local para enviarla luego
        password_plain = password

        # Buscar el usuario por id
        try:
            usuario = User.objects.get(id=user_id)
        except User.DoesNotExist:
            raise Exception("El usuario especificado no existe.")

        # Actualizar la contraseña en el usuario usando set_password (esto la cifrará)
        usuario.set_password(password_plain)
        usuario.save()

        # Verificar que el horario existe
        try:
            horario = Horario.objects.get(id=horario_id)
        except Horario.DoesNotExist:
            raise Exception("El horario especificado no existe.")

        # Crear el chofer asignándole el usuario encontrado
        chofer = Chofer(
            nombre=nombre,
            apellidos=apellidos,
            usuario=usuario,
            rfc=rfc,
            licencia=licencia,
            certificaciones=certificaciones,
            horario=horario,
            pin=None  # Se inicializa sin PIN
        )
        chofer.save()

        # Enviar correo electrónico con usuario y contraseña en texto plano
        sender_email = "logisticlogix0@gmail.com"  # Correo de envío
        app_password = "nzvi ailf xxck gctf"         # Contraseña de aplicación (ejemplo)
        subject = "Datos de acceso a la plataforma"
        body = (
            f"Estimado {chofer.nombre or usuario.username},\n\n"
            f"Su usuario es: {usuario.username}\n"
            f"Su contraseña es: {password_plain}\n\n"
            f"Bienvenido a la familia Logix. Dentro de la App podrás cambiar tu contraseña si así lo prefieres."
        )

        message = MIMEText(body, "plain")
        message["Subject"] = subject
        message["From"] = sender_email

        # Destinatario: email del usuario
        recipients = [usuario.email]

        try:
            # Enviar correo utilizando SMTP con SSL (en este ejemplo, Gmail)
            with smtplib.SMTP_SSL("smtp.gmail.com", 465) as server:
                server.login(sender_email, app_password)
                server.sendmail(sender_email, recipients, message.as_string())
        except Exception as e:
            print(f"Error al enviar el correo: {e}")

        return CreateChofer(chofer=chofer)

# Mutación para establecer el PIN del chofer
class SetChoferPin(graphene.Mutation):
    class Arguments:
        pin = graphene.String(required=True)

    chofer = graphene.Field(ChoferType)

    def mutate(self, info, pin):
        user = info.context.user
        if not user.is_authenticated:
            raise Exception("Debes estar autenticado para establecer un PIN.")

        try:
            chofer = Chofer.objects.get(usuario=user)
        except Chofer.DoesNotExist:
            raise Exception("No tienes permiso para establecer un PIN.")

        if not pin.isdigit() or len(pin) != 4:
            raise Exception("El PIN debe contener exactamente 4 dígitos numéricos.")

        if es_secuencial(pin):
            raise Exception("El PIN no puede ser una secuencia numérica.")

        chofer.pin = pin
        chofer.save()
        return SetChoferPin(chofer=chofer)

# Mutación para actualizar el PIN del chofer
class UpdateChoferPin(graphene.Mutation):
    class Arguments:
        pin = graphene.String(required=True)

    chofer = graphene.Field(ChoferType)

    def mutate(self, info, pin):
        user = info.context.user
        if not user.is_authenticated:
            raise Exception("Debes estar autenticado para editar el PIN.")

        try:
            chofer = Chofer.objects.get(usuario=user)
        except Chofer.DoesNotExist:
            raise Exception("No tienes permiso para editar el PIN.")

        if not pin.isdigit() or len(pin) != 4:
            raise Exception("El PIN debe contener exactamente 4 dígitos numéricos.")

        if es_secuencial(pin):
            raise Exception("El PIN no puede ser una secuencia numérica.")

        chofer.pin = pin
        chofer.save()
        return UpdateChoferPin(chofer=chofer)

# Definición de Mutaciones
class Mutation(graphene.ObjectType):
    create_chofer = CreateChofer.Field()
    set_chofer_pin = SetChoferPin.Field()
    update_chofer_pin = UpdateChoferPin.Field()

# Definición del esquema GraphQL
schema = graphene.Schema(query=Query, mutation=Mutation)

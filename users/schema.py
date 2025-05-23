import graphene
import graphql_jwt
import random
import string
from django.contrib.auth import get_user_model
from graphene_django import DjangoObjectType
from django.contrib.auth.tokens import default_token_generator
from django.utils.http import urlsafe_base64_encode, urlsafe_base64_decode
from django.utils.encoding import force_bytes, force_str
from email.mime.text import MIMEText
import smtplib
from django.conf import settings

User = get_user_model()

class UserType(DjangoObjectType):
    class Meta:
        model = User
        exclude = ('password',)

def make_temp_password(length=10):
    chars = string.ascii_letters + string.digits
    return ''.join(random.choice(chars) for _ in range(length))

# ————————————————————————————————————————
# Mutación 1: registro normal (usuario elige contraseña)
# ————————————————————————————————————————
class CreateUser(graphene.Mutation):
    user = graphene.Field(UserType)

    class Arguments:
        username = graphene.String(required=True)
        password = graphene.String(required=True)
        email    = graphene.String(required=True)

    def mutate(self, info, username, password, email):
        user = User.objects.create_user(
            username=username,
            email=email,
            password=password,
            is_active=True
        )
        return CreateUser(user=user)

# ————————————————————————————————————————
# Mutación 2: creación con contraseña temporal
# ————————————————————————————————————————
class CreateUserWithTempPassword(graphene.Mutation):
    user         = graphene.Field(UserType)
    tempPassword = graphene.String()

    class Arguments:
        username = graphene.String(required=True)
        email    = graphene.String(required=True)

    def mutate(self, info, username, email):
        # 1) Generar contraseña temporal
        temp_pass = make_temp_password()

        # 2) Crear usuario activo con esa contraseña
        user = User.objects.create_user(
            username=username,
            email=email,
            password=temp_pass,
            is_active=True,
        )

        # 3) Enviar correo con credenciales
        sender_email = "logisticlogix0@gmail.com"
        app_password = "nzvi ailf xxck gctf"
        subject      = "Datos de acceso a la plataforma"
        body = (
            f"Estimado {username},\n\n"
            f"Su usuario es: {username}\n"
            f"Su contraseña temporal es: {temp_pass}\n\n"
            "Bienvenido a la familia Logix. Podrás cambiar tu contraseña en la App."
        )
        message = MIMEText(body, "plain")
        message["Subject"] = subject
        message["From"]    = sender_email
        message["To"]      = email

        try:
            with smtplib.SMTP_SSL("smtp.gmail.com", 465) as server:
                server.login(sender_email, app_password)
                server.sendmail(sender_email, [email], message.as_string())
        except Exception as e:
            print(f"Error al enviar el correo: {e}")

        # 4) Devolver user + temp_pass al cliente
        return CreateUserWithTempPassword(user=user, tempPassword=temp_pass)

# ————————————————————————————————————————
# Reset de contraseña como antes
# ————————————————————————————————————————
class SendPasswordResetEmail(graphene.Mutation):
    ok = graphene.Boolean()
    class Arguments:
        email = graphene.String(required=True)
    def mutate(self, info, email):
        try:
            user = User.objects.get(email=email)
        except User.DoesNotExist:
            return SendPasswordResetEmail(ok=True)
        uidb64 = urlsafe_base64_encode(force_bytes(user.pk))
        token  = default_token_generator.make_token(user)
        reset_link = f"https://tudominio.com/reset-password/{uidb64}/{token}/"
        sender_email = "logisticlogix0@gmail.com"
        app_password = "nzvi ailf xxck gctf"
        subject = "Restablece tu contraseña"
        body = (
            f"Hola {user.username},\n\n"
            "Para restablecer tu contraseña, haz clic en el siguiente enlace:\n\n"
            f"{reset_link}\n\n"
            "Si no solicitaste este correo, ignóralo."
        )
        message = MIMEText(body, "plain")
        message["Subject"] = subject
        message["From"]    = sender_email
        message["To"]      = user.email
        try:
            with smtplib.SMTP_SSL("smtp.gmail.com", 465) as server:
                server.login(sender_email, app_password)
                server.sendmail(sender_email, [user.email], message.as_string())
        except Exception as e:
            print(f"Error al enviar reset email: {e}")
        return SendPasswordResetEmail(ok=True)

class ResetPassword(graphene.Mutation):
    ok = graphene.Boolean()
    class Arguments:
        uidb64       = graphene.String(required=True)
        token        = graphene.String(required=True)
        new_password = graphene.String(required=True)
    def mutate(self, info, uidb64, token, new_password):
        try:
            uid  = force_str(urlsafe_base64_decode(uidb64))
            user = User.objects.get(pk=uid)
        except Exception:
            raise Exception("Enlace inválido o usuario no encontrado.")
        if not default_token_generator.check_token(user, token):
            raise Exception("Token inválido o expirado.")
        user.set_password(new_password)
        user.save()
        return ResetPassword(ok=True)

class DirectPasswordReset(graphene.Mutation):
    ok = graphene.Boolean()
    class Arguments:
        username     = graphene.String(required=True)
        new_password = graphene.String(required=True)
    def mutate(self, info, username, new_password):
        try:
            user = User.objects.get(username=username)
        except User.DoesNotExist:
            raise Exception("Usuario no encontrado.")
        user.set_password(new_password)
        user.save()
        return DirectPasswordReset(ok=True)

# ————————————————————————————————————————
# JWT y Queries
# ————————————————————————————————————————
class Query(graphene.ObjectType):
    users = graphene.List(UserType)
    me    = graphene.Field(UserType)
    def resolve_users(self, info):
        return User.objects.all()
    @graphql_jwt.decorators.login_required
    def resolve_me(self, info):
        return info.context.user

class Mutation(graphene.ObjectType):
    # Registro normal
    create_user               = CreateUser.Field()
    # Registro con temp password
    create_user_with_temp_pwd = CreateUserWithTempPassword.Field()
    # Reset de pwd
    send_password_reset       = SendPasswordResetEmail.Field()
    reset_password            = ResetPassword.Field()
    direct_password_reset     = DirectPasswordReset.Field()
    # JWT
    token_auth    = graphql_jwt.ObtainJSONWebToken.Field()
    verify_token  = graphql_jwt.Verify.Field()
    refresh_token = graphql_jwt.Refresh.Field()

schema = graphene.Schema(query=Query, mutation=Mutation)

import graphene
from django.contrib.auth import get_user_model
from graphene_django import DjangoObjectType
from graphql_jwt.decorators import login_required  # Para proteger resolvers
from django.contrib.auth.tokens import default_token_generator
from django.utils.http import urlsafe_base64_encode, urlsafe_base64_decode
from django.utils.encoding import force_bytes, force_str
from email.mime.text import MIMEText
import smtplib

User = get_user_model()

class UserType(DjangoObjectType):
    class Meta:
        model = User

class CreateUser(graphene.Mutation):
    user = graphene.Field(UserType)

    class Arguments:
        username = graphene.String(required=True)
        password = graphene.String(required=True)
        email = graphene.String(required=True)

    def mutate(self, info, username, password, email):
        user = User.objects.create_user(
            username=username,
            email=email,
            password=password
        )
        return CreateUser(user=user)

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
        token = default_token_generator.make_token(user)
        reset_link = f"https://tudominio.com/reset-password/{uidb64}/{token}/"

        subject = "Restablece tu contraseña"
        body = (
            f"Hola {user.username},\n\n"
            f"Para restablecer tu contraseña, haz clic en el siguiente enlace:\n\n"
            f"{reset_link}\n\n"
            "Si no solicitaste este correo, ignóralo."
        )
        message = MIMEText(body, "plain")
        message["Subject"] = subject
        message["From"] = "no-reply@tudominio.com"
        message["To"] = user.email

        try:
            with smtplib.SMTP_SSL("smtp.gmail.com", 465) as server:
                server.login("no-reply@tudominio.com", "TU_APP_PASSWORD")
                server.sendmail(message["From"], [message["To"]], message.as_string())
        except Exception as e:
            pass

        return SendPasswordResetEmail(ok=True)

class ResetPassword(graphene.Mutation):
    ok = graphene.Boolean()

    class Arguments:
        uidb64 = graphene.String(required=True)
        token = graphene.String(required=True)
        new_password = graphene.String(required=True)

    def mutate(self, info, uidb64, token, new_password):
        try:
            uid = force_str(urlsafe_base64_decode(uidb64))
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
        username = graphene.String(required=True)
        new_password = graphene.String(required=True)

    def mutate(self, info, username, new_password):
        try:
            user = User.objects.get(username=username)
        except User.DoesNotExist:
            raise Exception("Usuario no encontrado.")

        user.set_password(new_password)
        user.save()
        return DirectPasswordReset(ok=True)

class Query(graphene.ObjectType):
    users = graphene.List(UserType)
    me = graphene.Field(UserType)

    def resolve_users(self, info):
        return User.objects.all()

    @login_required
    def resolve_me(self, info):
        return info.context.user

class Mutation(graphene.ObjectType):
    create_user = CreateUser.Field()
    send_password_reset = SendPasswordResetEmail.Field()
    reset_password = ResetPassword.Field()
    direct_password_reset = DirectPasswordReset.Field()

schema = graphene.Schema(query=Query, mutation=Mutation)

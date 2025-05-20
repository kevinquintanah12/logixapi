import graphene
import graphql_jwt
from django.contrib.auth import get_user_model
from graphene_django import DjangoObjectType
from django.utils.http import urlsafe_base64_encode, urlsafe_base64_decode
from django.utils.encoding import force_bytes, force_str
from django.contrib.auth.tokens import default_token_generator
from django.core.mail import send_mail
from django.conf import settings

User = get_user_model()

class UserType(DjangoObjectType):
    class Meta:
        model = User
        exclude = ('password',)  # nunca exponemos el hash

# ────────────────────────────────────────────
# MUTATION: CREAR USUARIO + ENLACE DE ACTIVACIÓN
# ────────────────────────────────────────────
class CreateUser(graphene.Mutation):
    ok = graphene.Boolean()

    class Arguments:
        username = graphene.String(required=True)
        email    = graphene.String(required=True)

    def mutate(self, info, username, email):
        # 1) Crear usuario inactivo, sin contraseña
        user = User.objects.create_user(
            username=username,
            email=email,
            password=None,      # contraseña vacía
            is_active=False     # no activo hasta validar
        )

        # 2) Generar token y enlace
        uidb64 = urlsafe_base64_encode(force_bytes(user.pk))
        token  = default_token_generator.make_token(user)
        activation_link = f"https://tudominio.com/activate/{uidb64}/{token}"

        # 3) Enviar correo
        subject = "Activa tu cuenta"
        message = (
            f"Hola {username},\n\n"
            f"Para activar tu cuenta, haz clic en el siguiente enlace:\n\n"
            f"{activation_link}\n\n"
            "Si no solicitaste esto, ignora este correo."
        )
        send_mail(
            subject,
            message,
            settings.DEFAULT_FROM_EMAIL,
            [email],
            fail_silently=False,
        )

        return CreateUser(ok=True)

# ────────────────────────────────────────────
# MUTATION: ACTIVAR CUENTA + SETEAR CONTRASEÑA
# ────────────────────────────────────────────
class ActivateUser(graphene.Mutation):
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

        # Activar y setear contraseña
        user.set_password(new_password)
        user.is_active = True
        user.save()

        return ActivateUser(ok=True)

# ────────────────────────────────────────────
# SCHEMA
# ────────────────────────────────────────────
class Query(graphene.ObjectType):
    me    = graphene.Field(UserType)
    users = graphene.List(UserType)

    @login_required
    def resolve_me(self, info):
        return info.context.user

    def resolve_users(self, info):
        return User.objects.filter(is_active=True)

class Mutation(graphene.ObjectType):
    # Creación + activación
    create_user   = CreateUser.Field()
    activate_user = ActivateUser.Field()

    # JWT
    token_auth   = graphql_jwt.ObtainJSONWebToken.Field()
    verify_token = graphql_jwt.Verify.Field()
    refresh_token= graphql_jwt.Refresh.Field()

schema = graphene.Schema(query=Query, mutation=Mutation)

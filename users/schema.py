import graphene
import graphql_jwt
import random, string
from django.contrib.auth import get_user_model
from graphene_django import DjangoObjectType
from django.core.mail import send_mail
from django.conf import settings

User = get_user_model()

class UserType(DjangoObjectType):
    class Meta:
        model = User
        exclude = ('password',)

def make_temp_password(length=10):
    # Genera una cadena de letras+números aleatoria
    chars = string.ascii_letters + string.digits
    return ''.join(random.choice(chars) for _ in range(length))

class CreateUser(graphene.Mutation):
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

        # 3) Enviar email con la contraseña
        subject = "Tu cuenta está lista"
        message = (
            f"Hola {username},\n\n"
            "Tu cuenta ha sido creada. Estos son tus datos:\n\n"
            f"Usuario: {username}\n"
            f"Contraseña temporal: {temp_pass}\n\n"
            "Podrás cambiarla luego desde tu perfil."
        )
        send_mail(
            subject,
            message,
            settings.DEFAULT_FROM_EMAIL,
            [email],
            fail_silently=False,
        )

        # 4) Devolver user + temp_pass al cliente
        return CreateUser(user=user, tempPassword=temp_pass)

class Query(graphene.ObjectType):
    me    = graphene.Field(UserType)
    users = graphene.List(UserType)

    @graphql_jwt.decorators.login_required
    def resolve_me(self, info):
        return info.context.user

    def resolve_users(self, info):
        return User.objects.filter(is_active=True)

class Mutation(graphene.ObjectType):
    create_user   = CreateUser.Field()
    token_auth    = graphql_jwt.ObtainJSONWebToken.Field()
    verify_token  = graphql_jwt.Verify.Field()
    refresh_token = graphql_jwt.Refresh.Field()

schema = graphene.Schema(query=Query, mutation=Mutation)

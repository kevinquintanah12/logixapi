import graphene
from django.contrib.auth import get_user_model
from graphene_django import DjangoObjectType
from graphql_jwt.decorators import login_required  # Importar el decorador para autenticación

class UserType(DjangoObjectType):
    class Meta:
        model = get_user_model()

class CreateUser(graphene.Mutation):
    user = graphene.Field(UserType)

    class Arguments:
        username = graphene.String(required=True)
        password = graphene.String(required=True)
        email = graphene.String(required=True)

    def mutate(self, info, username, password, email):
        user = get_user_model().objects.create_user(
            username=username,
            email=email,
            password=password  # Aquí asignamos la contraseña correctamente
        )
        return CreateUser(user=user)

class Query(graphene.ObjectType):
    users = graphene.List(UserType)
    me = graphene.Field(UserType)  # Consulta para obtener el usuario autenticado

    def resolve_users(self, info):
        return get_user_model().objects.all()

    @login_required  # Requiere autenticación para obtener el usuario autenticado
    def resolve_me(self, info):
        return info.context.user  # Obtiene el usuario a partir del token JWT

class Mutation(graphene.ObjectType):
    create_user = CreateUser.Field()

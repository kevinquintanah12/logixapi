import graphene
from graphene_django.types import DjangoObjectType
from .models import FCMDevice
from graphql_jwt.decorators import login_required

class FCMDeviceType(DjangoObjectType):
    class Meta:
        model = FCMDevice
        fields = ('id', 'token', 'created_at')

# Definir una Query si se requiere
class Query(graphene.ObjectType):
    fcm_devices = graphene.List(FCMDeviceType)

    @login_required
    def resolve_fcm_devices(self, info):
        user = info.context.user
        return FCMDevice.objects.filter(user=user)

# Mutación para guardar o actualizar el token FCM
class GuardarTokenFCM(graphene.Mutation):
    class Arguments:
        token = graphene.String(required=True)

    ok = graphene.Boolean()

    @login_required
    def mutate(self, info, token):
        user = info.context.user
        FCMDevice.objects.update_or_create(
            user=user,
            defaults={'token': token},
        )
        return GuardarTokenFCM(ok=True)

# Renombramos FCMMutation a Mutation para que sea accesible como se espera
class Mutation(graphene.ObjectType):
    guardar_token_fcm = GuardarTokenFCM.Field()

# Finalmente, definimos el esquema que integre Query y Mutation
schema = graphene.Schema(query=Query, mutation=Mutation)

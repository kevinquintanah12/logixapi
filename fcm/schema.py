import graphene
from graphene_django.types import DjangoObjectType
from .models import FCMDevice
from graphql_jwt.decorators import login_required

class FCMDeviceType(DjangoObjectType):
    class Meta:
        model = FCMDevice
        fields = ('id', 'token', 'created_at')

class GuardarTokenFCM(graphene.Mutation):
    class Arguments:
        token = graphene.String(required=True)

    ok = graphene.Boolean()

    @login_required
    def mutate(self, info, token):
        user = info.context.user

        # Reemplazar o crear token
        FCMDevice.objects.update_or_create(
            user=user,
            token=token,
            defaults={'token': token},
        )

        return GuardarTokenFCM(ok=True)

class FCMMutation(graphene.ObjectType):
    guardar_token_fcm = GuardarTokenFCM.Field()

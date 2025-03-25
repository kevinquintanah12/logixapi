import graphene
import graphql_jwt

import users.schema
import roles_y_permisos.schema
import tipoproductos.schema
import tipoproductos.schema
import Ubicacion.schema
import calcularenvio.schema
import centrodistribucion.schema
import horarios.schema
import chofer.schema
import cliente.schema
import destinatario.schema
import producto.schema
import paquete.schema
class Query(users.schema.Query,  paquete.schema.Query, producto.schema.Query, destinatario.schema.Query,cliente.schema.Query, chofer.schema.Query, horarios.schema.Query, centrodistribucion.schema.Query, roles_y_permisos.schema.Query, tipoproductos.schema.Query, Ubicacion.schema.Query,calcularenvio.schema.Query,graphene.ObjectType):
    pass

class Mutation(users.schema.Mutation, paquete.schema.Mutation, producto.schema.Mutation, destinatario.schema.Mutation,cliente.schema.Mutation,chofer.schema.Mutation, horarios.schema.Mutation, centrodistribucion.schema.Mutation,  roles_y_permisos.schema.Mutation,tipoproductos.schema.Mutation, Ubicacion.schema.Mutation,calcularenvio.schema.Mutation, graphene.ObjectType):
    token_auth = graphql_jwt.ObtainJSONWebToken.Field()
    verify_token = graphql_jwt.Verify.Field()
    refresh_token = graphql_jwt.Refresh.Field()
schema = graphene.Schema(query=Query, mutation=Mutation)

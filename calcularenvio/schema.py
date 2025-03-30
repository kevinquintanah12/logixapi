import graphene
from graphene_django import DjangoObjectType
from graphql_jwt.decorators import login_required
from decimal import Decimal
from .models import CalcularEnvio
from tipoproductos.models import TipoProducto, Temperatura, Humedad
import requests
import math
import smtplib
from email.message import EmailMessage
from Ubicacion.models import Ubicacion

MAPBOX_ACCESS_TOKEN = "pk.eyJ1IjoiZGF5a2V2MTIiLCJhIjoiY204MTd5NzR3MGdxYTJqcGlsa29odnQ5YiJ9.tbAEt453VxfJoDatpU72YQ"

class CalcularEnvioType(DjangoObjectType):
    class Meta:
        model = CalcularEnvio
        fields = "__all__"

    def resolve_total_tarifa(self, info):
        return self.total_tarifa

    def resolve_tarifa_por_km(self, info):
        return self.tarifa_por_km

    def resolve_tarifa_peso(self, info):
        return self.tarifa_peso

    def resolve_distancia_km(self, info):
        return self.distancia_km

class Query(graphene.ObjectType):
    calcular_envio = graphene.Field(CalcularEnvioType, id=graphene.Int(required=True))
    ultimo_calculo = graphene.Field(CalcularEnvioType)
    enviar_ultimo_calculo_email = graphene.Field(
        CalcularEnvioType, email=graphene.String(required=True)
    )

    def resolve_calcular_envio(self, info, id):
        return CalcularEnvio.objects.get(id=id)

    def resolve_ultimo_calculo(self, info):
        return CalcularEnvio.objects.latest('id')

    @login_required
    def resolve_enviar_ultimo_calculo_email(self, info, email):
        # Obtener el último cálculo de envío
        ultimo_calculo = CalcularEnvio.objects.latest('id')
        
        # Construir el mensaje con detalles del envío
        subject = "Detalles de tu último cálculo de envío"
        body = (
            f"Hola,\n\n"
            f"A continuación, se muestran los detalles de tu último cálculo de envío:\n"
            f"- Origen: {ultimo_calculo.origen_cd.nombre}\n"
            f"- Destino: {ultimo_calculo.destino.ciudad}\n"
            f"- Peso total: {ultimo_calculo.peso_unitario * ultimo_calculo.numero_piezas} kg\n"
            f"- Distancia: {ultimo_calculo.distancia_km:.2f} km\n"
            f"- Tarifa total: ${ultimo_calculo.total_tarifa:.2f} MXN\n\n"
            f"¡Gracias por utilizar nuestro servicio!"
        )
        
        # Configuración del remitente y credenciales del servidor SMTP
        sender_email = "kevinherreraq12@gmail.com"  # Debe ser una cuenta configurada para enviar emails
        smtp_token = "yoaum dpve cwwx rhmyo"  # Puede ser la contraseña o token de aplicación
        smtp_server = "smtp.gmail.com"  # Ejemplo con Gmail
        smtp_port = 587  # Puerto para TLS

        # Construcción del email utilizando EmailMessage
        msg = EmailMessage()
        msg.set_content(body)
        msg["Subject"] = subject
        msg["From"] = sender_email
        msg["To"] = email

        try:
            # Conexión al servidor SMTP con TLS y autenticación
            server = smtplib.SMTP(smtp_server, smtp_port)
            server.ehlo()
            server.starttls()
            server.ehlo()
            server.login(sender_email, smtp_token)
            server.send_message(msg)
            server.quit()
        except Exception as e:
            raise Exception("Error enviando email: " + str(e))
        
        # Retornar el último cálculo para confirmar la operación
        return ultimo_calculo

class CrearCalcularEnvio(graphene.Mutation):
    class Arguments:
        tipo_producto_id = graphene.Int(required=True)
        origen_cd_id = graphene.Int(required=True)
        destino_id = graphene.Int(required=True)
        peso_unitario = graphene.Float(required=True)
        numero_piezas = graphene.Int(required=True)
        dimensiones_largo = graphene.Float(required=True)
        dimensiones_ancho = graphene.Float(required=True)
        dimensiones_alto = graphene.Float(required=True)
        descripcion = graphene.String(required=True)
        envio_express = graphene.Boolean(required=True)

    calcular_envio = graphene.Field(CalcularEnvioType)

    @login_required
    def mutate(self, info, tipo_producto_id, origen_cd_id, destino_id, peso_unitario,
               numero_piezas, dimensiones_largo, dimensiones_ancho, dimensiones_alto,
               descripcion, envio_express):

        tipo_producto = TipoProducto.objects.get(id=tipo_producto_id)
        tarifa_base = Decimal(tipo_producto.precio_base)

        temperatura = Temperatura.objects.filter(tipo_producto_id=tipo_producto_id).first()
        tarifa_extra_temperatura = Decimal(temperatura.tarifa_extra) if temperatura else Decimal(0)

        humedad = Humedad.objects.filter(tipo_producto_id=tipo_producto_id).first()
        tarifa_extra_humedad = Decimal(humedad.tarifa_extra) if humedad else Decimal(0)

        origen = Ubicacion.objects.get(id=origen_cd_id)
        destino = Ubicacion.objects.get(id=destino_id)
        origen_coords = (origen.longitud, origen.latitud)
        destino_coords = (destino.longitud, destino.latitud)

        calcular_envio = CalcularEnvio.objects.create(
            tipo_producto_id=tipo_producto_id,
            origen_cd_id=origen_cd_id,
            destino_id=destino_id,
            peso_unitario=Decimal(peso_unitario),
            numero_piezas=numero_piezas,
            dimensiones_largo=Decimal(dimensiones_largo),
            dimensiones_ancho=Decimal(dimensiones_ancho),
            dimensiones_alto=Decimal(dimensiones_alto),
            tarifa_base=tarifa_base,
            tarifa_extra_temperatura=tarifa_extra_temperatura,
            tarifa_extra_humedad=tarifa_extra_humedad,
            trasladoiva=Decimal(0),
            ieps=Decimal(0),
            descripcion=descripcion,
            envio_express=envio_express
        )

        url = (
            f"https://api.mapbox.com/directions/v5/mapbox/driving/"
            f"{origen_coords[0]},{origen_coords[1]};{destino_coords[0]},{destino_coords[1]}"
        )
        params = {
            'access_token': MAPBOX_ACCESS_TOKEN,
            'geometries': 'geojson'
        }
        response = requests.get(url, params=params)
        data = response.json()
        if not data.get('routes'):
            raise Exception("No se pudo obtener la ruta desde Mapbox.")
        distance_meters = data['routes'][0]['distance']
        distance_km = distance_meters / 1000

        tramos = math.ceil(distance_km / 30)
        tarifa_por_km = Decimal(tramos * 4)
        tarifa_por_peso = Decimal(peso_unitario * numero_piezas) * Decimal(5)
        subtotal = tarifa_base + tarifa_extra_temperatura + tarifa_extra_humedad + tarifa_por_km + tarifa_por_peso
        iva_calculado = subtotal * Decimal('0.10')
        ieps_calculado = subtotal * Decimal('0.10')
        total_final = subtotal + iva_calculado + ieps_calculado

        if envio_express:
            total_final += Decimal(900)  # Se suman 900 pesos si es express

        calcular_envio.tarifa_por_km = tarifa_por_km
        calcular_envio.tarifa_peso = tarifa_por_peso
        calcular_envio.distancia_km = Decimal(distance_km)
        calcular_envio.trasladoiva = iva_calculado
        calcular_envio.ieps = ieps_calculado
        calcular_envio.total_tarifa = total_final
        calcular_envio.save()

        return CrearCalcularEnvio(calcular_envio=calcular_envio)

class Mutation(graphene.ObjectType):
    crear_calcular_envio = CrearCalcularEnvio.Field()

schema = graphene.Schema(query=Query, mutation=Mutation)

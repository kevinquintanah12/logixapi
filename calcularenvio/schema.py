import graphene
from graphene_django import DjangoObjectType
from graphql_jwt.decorators import login_required
from decimal import Decimal
from .models import CalcularEnvio
from tipoproductos.models import TipoProducto, Temperatura, Humedad
import requests
import math
import smtplib
from email.mime.text import MIMEText
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
        
        # Construir el contenido HTML del correo con una tabla de detalles
        subject = "Cotización de Envío - Detalles de Cotización"
        body = f"""
        <html>
        <head>
            <style>
                body {{
                    font-family: Arial, sans-serif;
                    background-color: #e9f7fe;
                    margin: 0;
                    padding: 20px;
                }}
                table {{
                    width: 100%;
                    border-collapse: collapse;
                    margin-top: 20px;
                }}
                th, td {{
                    padding: 15px 20px;
                    text-align: left;
                    border: 1px solid #ddd;
                    font-size: 18px;
                    font-weight: bold;
                }}
                th {{
                    background-color: #0066cc;
                    color: white;
                }}
                td {{
                    background-color: #f2f9fc;
                }}
                h2 {{
                    color: #0066cc;
                    font-size: 24px;
                }}
                p {{
                    font-size: 16px;
                    color: #333;
                }}
                ul {{
                    list-style-type: none;
                    padding: 0;
                }}
                ul li {{
                    font-size: 16px;
                    color: #333;
                }}
                .footer {{
                    margin-top: 30px;
                    font-size: 14px;
                    color: #666;
                }}
            </style>
        </head>
        <body>
            <h2>Estimado cliente,</h2>
            <p>A continuación, encontrará los detalles de su cotización de envío:</p>
            <table>
                <tr>
                    <th>Concepto</th>
                    <th>Detalle</th>
                </tr>
                <tr>
                    <td>Origen</td>
                    <td>{ultimo_calculo.origen_cd.ubicacion.ciudad}</td>
                </tr>
                <tr>
                    <td>Destino</td>
                    <td>{ultimo_calculo.destino.ciudad}</td>
                </tr>
                <tr>
                    <td>Tarifa por Km</td>
                    <td>{ultimo_calculo.tarifa_por_km}</td>
                </tr>
                <tr>
                    <td>Tarifa por Peso</td>
                    <td>{ultimo_calculo.tarifa_peso}</td>
                </tr>
                <tr>
                    <td>Tarifa Base</td>
                    <td>{ultimo_calculo.tarifa_base}</td>
                </tr>
                <tr>
                    <td>Tarifa Extra Temperatura</td>
                    <td>{ultimo_calculo.tarifa_extra_temperatura}</td>
                </tr>
                <tr>
                    <td>Tarifa Extra Humedad</td>
                    <td>{ultimo_calculo.tarifa_extra_humedad}</td>
                </tr>
                <tr>
                    <td>Traslado IVA</td>
                    <td>{ultimo_calculo.trasladoiva}</td>
                </tr>
                <tr>
                    <td>IEPS</td>
                    <td>{ultimo_calculo.ieps}</td>
                </tr>
                <tr>
                    <td>Total Tarifa</td>
                    <td>{ultimo_calculo.total_tarifa}</td>
                </tr>
            </table>
            <br>
            <p>Para cualquier duda o consulta, no dude en contactarnos:</p>
            <ul>
                <li>Teléfono: 2741431652</li>
                <li>Correo: logisticlogix0@gmail.com</li>
            </ul>
            <p class="footer">Agradecemos su preferencia.</p>
            <p class="footer">Atentamente,<br>Equipo Logistic Logix</p>
        </body>
        </html>
        """


        
        # Configuración del remitente y credenciales del servidor SMTP
        sender_email = "logisticlogix0@gmail.com"  # Correo de envío
        app_password = "nzvi ailf xxck gctf"  # Contraseña o token de aplicación
        
        # Crear el mensaje usando MIMEText con contenido HTML
        message = MIMEText(body, "html")
        message["Subject"] = subject
        message["From"] = sender_email
        message["To"] = email  # Se utiliza el parámetro recibido en la query
        
        try:
            # Conexión al servidor SMTP con SSL (Gmail)
            with smtplib.SMTP_SSL("smtp.gmail.com", 465) as server:
                server.login(sender_email, app_password)
                server.sendmail(sender_email, email, message.as_string())
                print("Correo enviado exitosamente")
        except Exception as e:
            print(f"Error al enviar el correo: {e}")
        
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

import firebase_admin
from firebase_admin import credentials, messaging
import os

# Ruta al archivo JSON que descargaste de Firebase
ruta_json = os.path.join(os.path.dirname(__file__), 'app-driver-d1bfb-firebase-adminsdk-fbsvc-3e566a3b4e.json')

# Inicialización de Firebase Admin SDK
if not firebase_admin._apps:
    cred = credentials.Certificate(ruta_json)
    firebase_admin.initialize_app(cred)

# Función para enviar una notificación push
def enviar_notificacion_fcm_v1(token, title, body):
    try:
        # Creación del mensaje
        message = messaging.Message(
            token=token,
            notification=messaging.Notification(
                title=title,
                body=body,
            )
        )
        # Enviar el mensaje
        response = messaging.send(message)
        print(f'Notificación enviada correctamente: {response}')
    except Exception as e:
        print(f'Error al enviar notificación: {e}')

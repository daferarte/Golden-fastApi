import paho.mqtt.client as mqtt
import json
import os

# --- Configuración del Broker MQTT ---
# Lee la dirección IP del broker desde las variables de entorno para más seguridad,
# o usa "192.168.0.100" como valor por defecto.
MQTT_BROKER_IP = os.getenv("MQTT_BROKER_IP", "192.168.0.100")
MQTT_PORT = int(os.getenv("MQTT_PORT", 1883))

class MQTTClient:
    """
    Gestiona la conexión y publicación de mensajes al broker MQTT.
    """
    def __init__(self):
        # Usamos la versión 2 de la API de callbacks, que es la más moderna.
        self.client = mqtt.Client(mqtt.CallbackAPIVersion.VERSION2, client_id="fastapi_backend_service")
        self.client.on_connect = self.on_connect
        self.client.on_disconnect = self.on_disconnect

    def on_connect(self, client, userdata, flags, rc, properties):
        """Función que se ejecuta al conectar exitosamente al broker."""
        if rc == 0:
            print("✅ Conectado exitosamente al Broker MQTT!")
        else:
            print(f"❌ Falló la conexión al Broker MQTT, código de retorno: {rc}")

    def on_disconnect(self, client, userdata, rc, properties):
        """Función que se ejecuta cuando se pierde la conexión."""
        print(f"🔌 Desconectado del Broker MQTT con resultado: {rc}")

    def connect(self):
        """Inicia la conexión con el broker en un hilo separado."""
        try:
            self.client.connect(MQTT_BROKER_IP, MQTT_PORT, 60)
            self.client.loop_start()  # Esto es crucial, maneja la red en segundo plano.
        except Exception as e:
            print(f"🔥 Error al intentar conectar con MQTT: {e}")

    def disconnect(self):
        """Detiene el hilo de red y se desconecta limpiamente."""
        self.client.loop_stop()
        self.client.disconnect()

    def publish(self, topic: str, payload: dict) -> bool:
        """
        Publica un mensaje (en formato de diccionario) a un topic específico.
        Retorna True si la publicación fue exitosa, False en caso contrario.
        """
        try:
            # Convertimos el diccionario a un string JSON para enviarlo.
            message = json.dumps(payload)
            result = self.client.publish(topic, message)
            
            # result.rc es 0 si fue exitoso.
            if result.rc == 0:
                print(f"✉️ Mensaje publicado en el topic '{topic}': {message}")
                return True
            else:
                print(f"⚠️ Falló al publicar en el topic '{topic}', código: {result.rc}")
                return False
        except Exception as e:
            print(f"🔥 Error durante la publicación del mensaje: {e}")
            return False

# Creamos una instancia única (Singleton) que será usada en toda la aplicación.
# Esto evita tener múltiples conexiones innecesarias.
mqtt_client = MQTTClient()

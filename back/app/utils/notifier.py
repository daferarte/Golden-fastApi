# app/utils/notifier.py
import json
import os
from paho.mqtt import publish

# Cargar configuración desde variables de entorno (.env)
BROKER_IPS = os.getenv("MQTT_BROKER_IPS", "127.0.0.1").split(",")
MQTT_PORT = int(os.getenv("MQTT_PORT", "1883"))
MQTT_USER = os.getenv("MQTT_USER", "backend")
MQTT_PASS = os.getenv("MQTT_PASS", "backendpass")

def notificar_asistencia(asistencia):
    """
    Envía un mensaje MQTT a todos los brokers configurados cuando se registra una asistencia.
    """
    try:
        cliente = asistencia.cliente
        payload = {
            "id": asistencia.id,
            "cliente": f"{cliente.nombre} {cliente.apellido}",
            "documento": cliente.documento,
            "foto": cliente.fotografia,
            "hora": asistencia.fecha_hora_entrada.isoformat(),
            "tipo": asistencia.tipo_acceso,
        }

        message = json.dumps(payload)

        for broker in BROKER_IPS:
            broker = broker.strip()
            if not broker:
                continue
            try:
                publish.single(
                    topic="asistencias/nueva",
                    payload=message,
                    hostname=broker,
                    port=MQTT_PORT,
                    auth={"username": MQTT_USER, "password": MQTT_PASS},
                )
                print(f"📡 MQTT -> {broker}:{MQTT_PORT} topic asistencias/nueva -> {payload['cliente']}")
            except Exception as e:
                print(f"⚠️ No se pudo notificar al broker {broker}: {e}")

    except Exception as e:
        print(f"⚠️ Error general enviando notificación MQTT: {e}")

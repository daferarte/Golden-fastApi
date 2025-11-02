# app/utils/notifier.py
import json
import os
from paho.mqtt import publish

# Cargar configuración desde variables de entorno (.env)
BROKER_IP = os.getenv("MQTT_BROKER_IP", "127.0.0.1")
MQTT_PORT = int(os.getenv("MQTT_PORT", "1883"))
MQTT_USER = os.getenv("MQTT_USER", "backend")
MQTT_PASS = os.getenv("MQTT_PASS", "backendpass")

# 🔹 Topic unificado con el frontend
TOPIC_EVENTO = "devices/pasto/gym/event"


def notificar_asistencia(asistencia):
    """
    Envía una notificación MQTT cuando se registra un acceso (permitido o denegado).
    Puede recibir:
      - Un objeto SQLAlchemy `Asistencia`, o
      - Un diccionario `payload` ya estructurado desde el servicio.
    """

    try:
        # 🧩 Caso 1: dict enriquecido
        if isinstance(asistencia, dict):
            payload = asistencia
        else:
            # 🧩 Caso 2: objeto Asistencia
            cliente = asistencia.cliente
            venta = getattr(asistencia, "venta", None)
            permitido = asistencia.motivo_error is None
            dias_restantes = None

            if venta and venta.fecha_fin:
                from datetime import date
                dias_restantes = (venta.fecha_fin - date.today()).days

            payload = {
                "permitido": permitido,
                "id_asistencia": asistencia.id,
                "nombre": f"{cliente.nombre} {cliente.apellido}".strip(),
                "documento": cliente.documento,
                "foto": cliente.fotografia,
                "hora": asistencia.fecha_hora_entrada.strftime("%H:%M:%S"),
                "tipo_acceso": asistencia.tipo_acceso,
                "tipo_membresia": venta.membresia.nombre_membresia if venta else None,
                "sesiones_restantes": venta.sesiones_restantes if venta else None,
                "dias_restantes": dias_restantes,
                "mensaje": (
                    f"Acceso permitido para {cliente.nombre}"
                    if permitido
                    else f"Acceso denegado: {asistencia.motivo_error}"
                ),
            }

        # 🚀 Publicar mensaje MQTT
        message = json.dumps(payload, ensure_ascii=False)
        publish.single(
            topic=TOPIC_EVENTO,
            payload=message,
            hostname=BROKER_IP,
            port=MQTT_PORT,
            auth={"username": MQTT_USER, "password": MQTT_PASS},
        )

        status = "✅" if payload.get("permitido") else "🚫"
        print(f"{status} MQTT -> {BROKER_IP}:{MQTT_PORT} [{payload['nombre']}] -> {payload['mensaje']}")

    except Exception as e:
        print(f"⚠️ Error enviando notificación MQTT: {e}")

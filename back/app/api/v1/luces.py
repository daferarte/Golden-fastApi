from fastapi import APIRouter
from app.schemas.colores import RGBColorRequest
from app.mqtt_client import mqtt_client
import json
import os

router = APIRouter()
CONFIG_FILE = "data/led_config.json"

# Asegurar que existe el directorio de datos
os.makedirs("data", exist_ok=True)

@router.get("/{sede}/{device}/rgb", response_model=RGBColorRequest)
def get_rgb_color(sede: str, device: str):
    """Obtiene el último color configurado para un dispositivo específico."""
    if os.path.exists(CONFIG_FILE):
        try:
            with open(CONFIG_FILE, "r") as f:
                data = json.load(f)
                # Buscamos la key "sede/device"
                key = f"{sede}/{device}"
                if key in data:
                    return RGBColorRequest(**data[key])
        except Exception:
            pass
    # Default: Apagado
    return RGBColorRequest(red=0, green=0, blue=0)

@router.post("/{sede}/{device}/rgb")
def set_rgb_color(sede: str, device: str, color: RGBColorRequest):
    """
    Guarda el color para un dispositivo específico y lo publica en MQTT.
    """
    # 1. Cargar configuración existente
    full_config = {}
    if os.path.exists(CONFIG_FILE):
        try:
            with open(CONFIG_FILE, "r") as f:
                full_config = json.load(f)
        except:
            full_config = {}

    # 2. Actualizar key específica
    key = f"{sede}/{device}"
    full_config[key] = color.dict()

    # 3. Guardar en archivo
    with open(CONFIG_FILE, "w") as f:
        json.dump(full_config, f, indent=2)

    # 4. Publicar en MQTT como COMANDO (igual que 'open_door')
    # Topic: devices/{sede}/{device}/cmd
    topic = f"devices/{sede}/{device}/cmd"
    
    # Estructura de Comando: { "action": "set_led", "red": 255, ... }
    payload = {
        "action": "set_led",
        **color.dict()
    }

    # Retain=False es lo estándar para comandos cmd
    mqtt_client.publish_json(
        topic=topic,
        payload=payload, 
        retain=False
    )

    return {"status": "ok", "message": f"Comando 'set_led' enviado a {key}", "color": color}

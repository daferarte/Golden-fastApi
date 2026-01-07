# app/main.py
from dotenv import load_dotenv
load_dotenv()  # ✅ Cargar .env antes de todo (MQTT, DB, etc.)

from fastapi import FastAPI, WebSocket, WebSocketDisconnect
from fastapi.middleware.cors import CORSMiddleware
from fastapi.middleware.gzip import GZipMiddleware
from fastapi.staticfiles import StaticFiles
from pathlib import Path
import logging
import asyncio
import time
import os
import json

from app.api.v1.api import api_router
from app.core.config import settings
from app.db.base import Base
from app.db.session import engine
from app.mqtt_client import mqtt_client
from app.services.event_broadcast import broadcaster


# ======================
#  Inicialización de Base de Datos
# ======================
def init_models():
    """Crea tablas si no existen (solo en entorno dev)."""
    try:
        Base.metadata.create_all(bind=engine)
        logging.getLogger("uvicorn").info("✅ DB models initialized (create_all).")
    except Exception as e:
        logging.getLogger("uvicorn.error").exception(f"❌ Error initializing DB models: {e}")


# ======================
#  Inicialización de Aplicación
# ======================
def get_application() -> FastAPI:
    """Crea la instancia principal de FastAPI con CORS, rutas y WebSocket."""
    app = FastAPI(
        title=settings.PROJECT_NAME,
        version="1.0.0"
    )

    # --- GZip Compression (Optimización) ---
    app.add_middleware(GZipMiddleware, minimum_size=1000)

    # --- CORS ---
    app.add_middleware(
        CORSMiddleware,
        allow_origins=[
            "http://192.168.101.21:5173",  # tu frontend real
            "http://localhost:5173",       # entorno local
            "*"
        ],
        allow_credentials=True,
        allow_methods=["*"],
        allow_headers=["*"],
    )

    # --- Routers REST ---
    app.include_router(api_router, prefix=settings.API_V1_STR)

    # --- Health checks ---
    @app.get("/health", tags=["Health"])
    def health():
        return {"status": "ok"}

    @app.get("/health/mqtt", tags=["Health"])
    def health_mqtt():
        """Verifica si el cliente MQTT está conectado."""
        return {"mqtt_connected": mqtt_client._connected.is_set()}

    # --- WebSocket global para eventos ---
    @app.websocket("/ws/events")
    async def websocket_events(ws: WebSocket):
        """Mantiene una conexión WebSocket viva para notificaciones en tiempo real."""
        await broadcaster.connect(ws)
        print(f"🔗 Nuevo cliente WebSocket conectado: {ws.client}")
        try:
            while True:
                try:
                    # Mantiene la conexión viva enviando pings cada 30s
                    await asyncio.wait_for(ws.receive_text(), timeout=30.0)
                except asyncio.TimeoutError:
                    await ws.send_text("ping")
        except WebSocketDisconnect:
            broadcaster.disconnect(ws)
            print("🔌 Cliente WebSocket desconectado")

    return app


# ======================
#  App principal
# ======================
app = get_application()

# --- Archivos estáticos (media) ---
MEDIA_ROOT = Path(__file__).resolve().parent.parent / "media"
MEDIA_ROOT.mkdir(parents=True, exist_ok=True)
app.mount("/media", StaticFiles(directory=str(MEDIA_ROOT)), name="media")


# ======================
#  Eventos del ciclo de vida
# ======================
@app.on_event("startup")
def on_startup():
    """Inicializa la base, MQTT y suscripciones."""
    logging.getLogger("uvicorn").info(f"📂 MEDIA_ROOT -> {MEDIA_ROOT}")

    if getattr(settings, "ENVIRONMENT", "development") == "development":
        init_models()

    try:
        print("🚀 Conectando al broker MQTT...")
        mqtt_client.connect()
        mqtt_client.ensure_sub("devices/pasto/gym/event")
        print("✅ Suscrito al topic devices/pasto/gym/event")

        # Restaurar Estado de Luces (Configuración Dinámica)
        if os.path.exists("data/led_config.json"):
            try:
                with open("data/led_config.json", "r") as f:
                    data = json.load(f)
                    # Iteramos por cada dispositivo configurado (key = "sede/device")
                    for key_device, payload in data.items():
                        if isinstance(payload, dict):
                            topic = f"devices/{key_device}/cmd"
                            # Envolvemos como comando 'set_led'
                            cmd_payload = {"action": "set_led", **payload}
                            mqtt_client.publish_json(topic, cmd_payload, retain=False)
                            print(f"💡 Restaurado via cmd [{topic}]: {cmd_payload}")
            except Exception as e:
                print(f"⚠️ Error restaurando luces: {e}")
    except Exception as e:
        logging.getLogger("uvicorn.error").exception(
            f"❌ No se pudo conectar a MQTT en startup: {e}"
        )


@app.on_event("shutdown")
def on_shutdown():
    """Cierra las conexiones MQTT y limpia recursos."""
    try:
        print("🔌 Desconectando del broker MQTT...")
        mqtt_client.disconnect()
        print("✅ MQTT desconectado correctamente")
    except Exception as e:
        logging.getLogger("uvicorn.error").exception(
            f"❌ Error al desconectar MQTT en shutdown: {e}"
        )

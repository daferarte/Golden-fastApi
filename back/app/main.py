# app/main.py
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles
from pathlib import Path
import logging

from app.api.v1.api import api_router
from app.core.config import settings
from app.db.base import Base
from app.db.session import engine

# --- MQTT ---
from app.mqtt_client import mqtt_client

# ======================
#  Helpers inicialización
# ======================
def init_models():
    try:
        Base.metadata.create_all(bind=engine)
        logging.getLogger("uvicorn").info("DB models initialized (create_all).")
    except Exception as e:
        logging.getLogger("uvicorn.error").exception(f"Error initializing DB models: {e}")

def get_application() -> FastAPI:
    app = FastAPI(
        title=settings.PROJECT_NAME,
        version="1.0.0"
    )

    # --- CORS ---
    app.add_middleware(
        CORSMiddleware,
        allow_origins=["http://10.162.248.224:5173", "*"],  # ajusta si quieres reforzar seguridad
        allow_credentials=True,
        allow_methods=["*"],
        allow_headers=["*"],
    )

    # --- Routers ---
    app.include_router(api_router, prefix=settings.API_V1_STR)

    # --- Rutas de salud básicas ---
    @app.get("/health", tags=["Health"])
    def health():
        return {"status": "ok"}

    @app.get("/health/mqtt", tags=["Health"])
    def health_mqtt():
        # Nota: esto solo indica si la sesión cree estar conectada.
        # Si necesitas un check profundo, puedes publicar a un topic de eco y esperar respuesta.
        return {"mqtt_connected": True if mqtt_client._connected.is_set() else False}

    return app

# ======================
#  App principal
# ======================
app = get_application()

# --- Media (estático) ---
MEDIA_ROOT = Path(__file__).resolve().parent.parent / "media"
MEDIA_ROOT.mkdir(parents=True, exist_ok=True)
app.mount("/media", StaticFiles(directory=str(MEDIA_ROOT)), name="media")

# ======================
#  Eventos de ciclo de vida
# ======================
@app.on_event("startup")
def on_startup():
    logging.getLogger("uvicorn").info(f"MEDIA_ROOT -> {MEDIA_ROOT}")
    if getattr(settings, "ENVIRONMENT", "development") == "development":
        init_models()

    # Conexión MQTT con manejo de errores (no bloquear API)
    try:
        print("🚀 Conectando al broker MQTT...")
        mqtt_client.connect()
    except Exception as e:
        # No frenar el arranque: loguear y continuar para que la API quede viva.
        logging.getLogger("uvicorn.error").exception(f"❌ No se pudo conectar a MQTT en startup: {e}")

@app.on_event("shutdown")
def on_shutdown():
    try:
        print("🔌 Desconectando del broker MQTT...")
        mqtt_client.disconnect()
    except Exception as e:
        logging.getLogger("uvicorn.error").exception(f"❌ Error al desconectar MQTT en shutdown: {e}")

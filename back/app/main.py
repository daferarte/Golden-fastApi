from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles
from pathlib import Path
from app.api.v1.api import api_router
from app.core.config import settings
from app.db.base import Base
from app.db.session import engine
import logging

# --- 1. IMPORTAMOS NUESTRO CLIENTE MQTT ---
from app.mqtt_client import mqtt_client

# Crear tablas si no existen (solo para desarrollo)
def init_models():
    Base.metadata.create_all(bind=engine)

def get_application() -> FastAPI:
    app = FastAPI(
        title=settings.PROJECT_NAME,
        version="1.0.0"
    )

    # Middleware CORS (tu configuración se mantiene intacta)
    app.add_middleware(
        CORSMiddleware,
        allow_origins=["http://10.162.248.224:5173", "*"],
        allow_credentials=True,
        allow_methods=["*"],
        allow_headers=["*"],
    )

    app.include_router(api_router, prefix=settings.API_V1_STR)
    return app

app = get_application()

# Ruta para archivos media (tu configuración se mantiene intacta)
MEDIA_ROOT = Path(__file__).resolve().parent.parent / "media"
MEDIA_ROOT.mkdir(parents=True, exist_ok=True)
app.mount("/media", StaticFiles(directory=str(MEDIA_ROOT)), name="media")

# --- 2. AÑADIMOS LA LÓGICA DE CONEXIÓN A TU EVENTO DE INICIO ---
@app.on_event("startup")
def on_startup():
    logging.getLogger("uvicorn").info(f"MEDIA_ROOT -> {MEDIA_ROOT}")
    if settings.ENVIRONMENT == "development":
        init_models()
    
    # Conectamos el cliente MQTT al arrancar la aplicación
    print("🚀 Iniciando conexión con el Broker MQTT...")
    mqtt_client.connect()

# --- 3. AÑADIMOS EL EVENTO DE APAGADO PARA DESCONECTAR MQTT ---
@app.on_event("shutdown")
def on_shutdown():
    # Desconectamos el cliente MQTT de forma segura al detener la aplicación
    print("🔌 Desconectando del Broker MQTT...")
    mqtt_client.disconnect()


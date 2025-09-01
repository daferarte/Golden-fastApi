from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware  # Importar middleware CORS
from fastapi.staticfiles import StaticFiles
from pathlib import Path
from app.api.v1.api import api_router
from app.core.config import settings
from app.db.base import Base
from app.db.session import engine  # sync engine
import logging

# Crear tablas si no existen (solo para desarrollo)
def init_models():
    Base.metadata.create_all(bind=engine)

def get_application() -> FastAPI:
    app = FastAPI(
        title=settings.PROJECT_NAME,
        version="1.0.0"
    )

    # Middleware CORS
    app.add_middleware(
        CORSMiddleware,
        allow_origins=["http://10.162.248.224:5173", "*"],  # o ["*"] en pruebas
        allow_credentials=True,
        allow_methods=["*"],
        allow_headers=["*"],
    )

    app.include_router(api_router, prefix=settings.API_V1_STR)
    return app

app = get_application()

# Ruta base: .../back/media
MEDIA_ROOT = Path(__file__).resolve().parent.parent / "media"
MEDIA_ROOT.mkdir(parents=True, exist_ok=True)
app.mount("/media", StaticFiles(directory=str(MEDIA_ROOT)), name="media")

# Evento de inicio de la app
@app.on_event("startup")
def on_startup():
    logging.getLogger("uvicorn").info(f"MEDIA_ROOT -> {MEDIA_ROOT}")
    if settings.ENVIRONMENT == "development":
        init_models()
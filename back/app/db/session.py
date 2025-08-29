from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker, Session
from app.core.config import settings

# Motor síncrono
engine = create_engine(
    settings.DATABASE_URL.replace("+asyncpg", ""),  # quita async si lo tienes
    echo=True,
    future=True
)

# Session maker síncrono
SessionLocal = sessionmaker(
    bind=engine,
    autoflush=False,
    autocommit=False
)

# Dependencia para FastAPI
def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()

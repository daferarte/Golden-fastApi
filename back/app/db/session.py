from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker, Session
from app.core.config import settings

# Motor síncrono
engine = create_engine(
    settings.DATABASE_URL.replace("+asyncpg", ""),  # quita async si lo tienes
    echo=(settings.ENVIRONMENT == "development"),
    future=True,
    pool_pre_ping=True,           # evita conexiones zombies
    pool_recycle=1800,            # < wait_timeout del server
    pool_size=10,
    max_overflow=20,
    connect_args={"charset": "utf8mb4"}
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

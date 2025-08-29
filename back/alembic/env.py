# alembic/env.py
import os
from logging.config import fileConfig

from alembic import context
from sqlalchemy import engine_from_config, pool, create_engine

# --- Carga de modelos para autogenerate ---
# Asegúrate de que app/models/__init__.py exponga Base
from app.models import Base

# --- Cargar .env primero (por si ejecutas fuera del servidor) ---
try:
    from dotenv import load_dotenv
    load_dotenv()
except Exception:
    # opcional: si no tienes python-dotenv instalado, ignora
    pass

# --- Config Alembic ---
config = context.config

# Habilita logging de alembic con alembic.ini
if config.config_file_name is not None:
    fileConfig(config.config_file_name)

# Metadata de tus modelos
target_metadata = Base.metadata

# --------- Utilidades ---------
def get_url() -> str:
    url = os.getenv("DATABASE_URL", "").strip()
    if not url:
        # Si no vino por env, intenta leer de alembic.ini (sqlalchemy.url)
        url = config.get_main_option("sqlalchemy.url", "").strip()
    if not url:
        raise RuntimeError(
            "DATABASE_URL no está definido y alembic.ini no tiene sqlalchemy.url. "
            "Define DATABASE_URL en tu entorno o en alembic.ini."
        )
    return url

# Opciones comunes de context.configure para MySQL
COMMON_OPTS = dict(
    target_metadata=target_metadata,
    compare_type=True,            # detecta cambios de tipo
    compare_server_default=True,  # detecta cambios en defaults
    render_as_batch=False,        # True solo si usas SQLite y necesitas batch
    include_schemas=False,        # pon True si manejas múltiples esquemas
)

# --------- Modo OFFLINE (genera SQL sin conectarse) ---------
def run_migrations_offline():
    url = get_url()
    context.configure(
        url=url,
        literal_binds=True,
        dialect_opts={"paramstyle": "named"},
        **COMMON_OPTS,
    )
    with context.begin_transaction():
        context.run_migrations()

# --------- Modo ONLINE (se conecta a la base y ejecuta) ---------
def run_migrations_online():
    url = get_url()

    # Puedes usar engine_from_config, pero create_engine es directo y claro
    connectable = create_engine(
        url,
        poolclass=pool.NullPool,
        # Opcionales útiles para MySQL:
        # future=True,  # si usas SQLAlchemy 2.x ya es por defecto en create_engine
    )

    with connectable.connect() as connection:
        context.configure(
            connection=connection,
            **COMMON_OPTS,
        )
        with context.begin_transaction():
            # Para MySQL, fuerza engine/collation por si tu metadata lo define:
            # target_metadata.info["mysql_default_engine"] = "InnoDB"
            # target_metadata.info["mysql_default_charset"] = "utf8mb4"
            context.run_migrations()

# --------- Punto de entrada ---------
if context.is_offline_mode():
    run_migrations_offline()
else:
    run_migrations_online()

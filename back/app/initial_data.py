
import logging
from app.db.session import SessionLocal
from app.models.rol import Rol
from app.models.usuario import Usuario
from app.core.security import get_password_hash

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

def init_db():
    db = SessionLocal()
    try:
        # 1. Crear Roles Iniciales
        roles_necesarios = ["dueño", "recepcionista", "entrenador", "entrenador_especial"]
        
        for nombre_rol in roles_necesarios:
            rol = db.query(Rol).filter(Rol.nombre_rol == nombre_rol).first()
            if not rol:
                nuevo_rol = Rol(nombre_rol=nombre_rol, descripcion=f"Rol de {nombre_rol}")
                db.add(nuevo_rol)
                logger.info(f"✅ Rol creado: {nombre_rol}")
            else:
                logger.info(f"🔹 Rol existente: {nombre_rol}")
        
        db.commit()

        # 2. Crear Superusuario (Dueño) Inicial si no existe
        rol_dueno = db.query(Rol).filter(Rol.nombre_rol == "dueño").first()
        admin_user = db.query(Usuario).filter(Usuario.nombre_usuario == "admin").first()
        
        if not admin_user and rol_dueno:
            admin_user = Usuario(
                nombre_usuario="admin",
                contraseña_hash=get_password_hash("admin123"),
                correo="admin@example.com",
                activo=True,
                id_rol=rol_dueno.id
            )
            db.add(admin_user)
            db.commit()
            logger.info("🚀 Usuario 'admin' creado con contraseña 'admin123'")
        else:
             logger.info("🔹 Usuario 'admin' ya existe")

    except Exception as e:
        logger.error(f"❌ Error inicializando datos: {e}")
    finally:
        db.close()

if __name__ == "__main__":
    print("Iniciando carga de datos iniciales...")
    init_db()
    print("Finalizado.")

from sqlalchemy.orm import joinedload
from app.models.usuario import Usuario
from .base import BaseRepository

class UsuarioRepository(BaseRepository):
    def __init__(self):
        super().__init__(Usuario)

    def get_all(self, db):
        return db.query(Usuario).options(joinedload(Usuario.rol)).all()

    def get_by_username(self, db, username: str):
        return db.query(Usuario).options(joinedload(Usuario.rol)).filter(Usuario.nombre_usuario == username).first()

from app.models.usuario import Usuario
from .base import BaseRepository

class UsuarioRepository(BaseRepository):
    def __init__(self):
        super().__init__(Usuario)

    def get_by_username(self, db, username: str):
        return db.query(Usuario).filter(Usuario.nombre_usuario == username).first()

from fastapi import HTTPException
from sqlalchemy.orm import Session
from app.repositories.usuario_repository import UsuarioRepository
from .base_service import BaseService

class UsuarioService(BaseService):
    def __init__(self):
        super().__init__(UsuarioRepository())

    def get_by_username(self, db: Session, username: str):
        user = self.repository.get_by_username(db, username)
        if not user:
            raise HTTPException(status_code=404, detail="Usuario no encontrado")
        return user

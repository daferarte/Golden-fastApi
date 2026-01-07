from fastapi import HTTPException
from sqlalchemy.orm import Session
from app.repositories.usuario_repository import UsuarioRepository
from app.core.security import get_password_hash
from app.models.usuario import Usuario
from .base_service import BaseService

class UsuarioService(BaseService):
    def __init__(self):
        super().__init__(UsuarioRepository())

    def create(self, db: Session, obj_in):
        # Convertimos Pydantic a dict
        user_data = obj_in.dict()
        # Extraemos la contraseña plana
        password_plain = user_data.pop("contraseña", None)
        
        if not password_plain:
             raise HTTPException(status_code=400, detail="La contraseña es requerida")

        # Hasheamos
        user_data["contraseña_hash"] = get_password_hash(password_plain)
        
        # Creamos el objeto modelo
        db_obj = Usuario(**user_data)
        
        db.add(db_obj)
        db.commit()
        db.refresh(db_obj)
        return db_obj

    def update(self, db: Session, id_value: int, obj_in):
        db_obj = self.repository.get_by_id(db, id_value)
        if not db_obj:
            raise HTTPException(status_code=404, detail="Usuario no encontrado")

        update_data = obj_in.dict(exclude_unset=True)
        
        # Si viene contraseña, la hasheamos y actualizamos contraseña_hash
        if "contraseña" in update_data:
            password_plain = update_data.pop("contraseña")
            update_data["contraseña_hash"] = get_password_hash(password_plain)

        for field, value in update_data.items():
            setattr(db_obj, field, value)

        db.add(db_obj)
        db.commit()
        db.refresh(db_obj)
        return db_obj

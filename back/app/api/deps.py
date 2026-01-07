from typing import Generator, Optional, List
from fastapi import Depends, HTTPException, status
from fastapi.security import OAuth2PasswordBearer
from jose import jwt, JWTError
from sqlalchemy.orm import Session
from pydantic import ValidationError

from app.core import security
from app.core.config import settings
from app.db.session import get_db
from app.models.usuario import Usuario
from app.services.usuario_service import UsuarioService

reusable_oauth2 = OAuth2PasswordBearer(
    tokenUrl=f"{settings.API_V1_STR}/auth/login"
)

usuario_service = UsuarioService()

def get_current_user(
    db: Session = Depends(get_db),
    token: str = Depends(reusable_oauth2)
) -> Usuario:
    """
    Valida el token JWT y recupera el usuario actual.
    """
    try:
        payload = jwt.decode(
            token, settings.secret_key, algorithms=[settings.algorithm]
        )
        username: str = payload.get("sub")
        if username is None:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="No se pudo validar las credenciales (sub missing)",
            )
    except (JWTError, ValidationError):
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Token inválido o expirado",
        )
    
    # Buscamos en repositorio usando el servicio (o repo directo)
    # NOTA: Usamos internal method del repositorio si el servicio no expone get_by_username públicamente tal cual,
    # pero arriba vimos que sí eliminé get_by_username del servicio.
    # Lo restauraré o usaré el repositorio directamente aquí para no complicar el servicio.
    # Mejor usar repository directo para deps puras.
    user = usuario_service.repository.get_by_username(db, username=username)
    
    if not user:
        raise HTTPException(status_code=404, detail="Usuario no encontrado")
    
    return user


def get_current_active_user(
    current_user: Usuario = Depends(get_current_user),
) -> Usuario:
    if not current_user.activo:
        raise HTTPException(status_code=400, detail="Usuario inactivo")
    return current_user


class RoleChecker:
    def __init__(self, allowed_roles: List[str]):
        """
        allowed_roles: lista de nombres de rol permitidos (ej: ["admin", "entrenador"]).
        """
        self.allowed_roles = allowed_roles

    def __call__(self, user: Usuario = Depends(get_current_active_user)):
        # Si no tiene rol asignado o el nombre del rol no está en la lista -> 403
        if not user.rol or user.rol.nombre_rol not in self.allowed_roles:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="No tiene permisos suficientes para realizar esta acción"
            )
        return user
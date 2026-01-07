from datetime import timedelta
from typing import Any

from fastapi import APIRouter, Depends, HTTPException, status
from fastapi.security import OAuth2PasswordRequestForm
from sqlalchemy.orm import Session

from app.db.session import get_db
from app.core import security
from app.services.usuario_service import UsuarioService
from app.schemas.token import Token

router = APIRouter()
usuario_service = UsuarioService()

@router.post("/login", response_model=Token)
def login_access_token(
    db: Session = Depends(get_db),
    form_data: OAuth2PasswordRequestForm = Depends()
) -> Any:
    """
    OAuth2 compatible token login, get an access token for future requests.
    """
    # 1. Buscar usuario
    user = usuario_service.repository.get_by_username(db, form_data.username)
    
    # 2. Validar usuario y contraseña
    if not user or not security.verify_password(form_data.password, user.contraseña_hash):
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Usuario o contraseña incorrectos",
            headers={"WWW-Authenticate": "Bearer"},
        )
    
    if not user.activo:
        raise HTTPException(status_code=400, detail="Usuario inactivo")

    # 3. Generar Access Token
    access_token_expires = timedelta(minutes=60 * 24) # 1 día ejemplo, configurable
    access_token = security.create_access_token(
        data={"sub": user.nombre_usuario},
        expires_delta=access_token_expires,
    )
    
    return {
        "access_token": access_token,
        "token_type": "bearer",
    }

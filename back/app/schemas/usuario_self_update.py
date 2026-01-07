from pydantic import BaseModel, EmailStr
from typing import Optional

class UsuarioSelfUpdate(BaseModel):
    nombre_usuario: Optional[str] = None
    correo: Optional[EmailStr] = None
    contraseña: Optional[str] = None

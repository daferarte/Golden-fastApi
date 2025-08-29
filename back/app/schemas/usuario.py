from pydantic import BaseModel, EmailStr
from typing import Optional

class UsuarioBase(BaseModel):
    nombre_usuario: str
    contraseña_hash: str
    correo: EmailStr
    activo: bool
    id_rol: int
    id_cliente: Optional[int]

class UsuarioCreate(UsuarioBase):
    pass

class UsuarioUpdate(UsuarioBase):
    pass

class UsuarioResponse(UsuarioBase):
    id: int
    class Config:
        orm_mode = True

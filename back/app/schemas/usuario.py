from pydantic import BaseModel, EmailStr
from typing import Optional
from app.schemas.rol import RolResponse

class UsuarioBase(BaseModel):
    nombre_usuario: str
    correo: EmailStr
    activo: bool = True
    id_rol: Optional[int] = None
    id_cliente: Optional[int] = None

class UsuarioCreate(UsuarioBase):
    contraseña: str  # Se recibe en texto plano

class UsuarioUpdate(BaseModel):
    nombre_usuario: Optional[str] = None
    correo: Optional[EmailStr] = None
    activo: Optional[bool] = None
    id_rol: Optional[int] = None
    id_cliente: Optional[int] = None
    contraseña: Optional[str] = None # Opcional para actualizar password

class UsuarioResponse(UsuarioBase):
    id: int
    rol: Optional[RolResponse] = None # <-- Agregamos el objeto anidado
    # No devolvemos la contraseña hash
    
    class Config:
        from_attributes = True  # Pydantic v2 usa from_attributes en lugar de orm_mode

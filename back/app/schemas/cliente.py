from pydantic import BaseModel, EmailStr, field_serializer
from typing import Optional
from datetime import date
import base64

class ClienteBase(BaseModel):
    nombre: str
    apellido: str
    documento: str
    fecha_nacimiento: date
    telefono: Optional[str] = None
    correo: EmailStr
    direccion: Optional[str] = None
    fotografia: Optional[str] = None
    id_tipo_descuento: Optional[int] = None
    id_huella: Optional[int] = None

class ClienteCreateRequest(ClienteBase):
    huella_template: Optional[str] = None

class ClienteCreate(ClienteBase):
    huella_template: Optional[bytes] = None

class ClienteUpdate(ClienteBase):
    huella_template: Optional[str] = None

class ClienteResponse(ClienteBase):
    id: int
    huella_template: Optional[bytes] = None

    @field_serializer('huella_template')
    def serialize_huella(self, huella: Optional[bytes], _info) -> Optional[str]:
        if huella is None:
            return None
        return base64.b64encode(huella).decode('utf-8')

    class Config:
        from_attributes = True

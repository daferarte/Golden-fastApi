from pydantic import BaseModel
from typing import Optional

class RolBase(BaseModel):
    nombre_rol: str
    descripcion: Optional[str]

class RolCreate(RolBase):
    pass

class RolUpdate(RolBase):
    pass

class RolResponse(RolBase):
    id: int
    class Config:
        from_attributes = True

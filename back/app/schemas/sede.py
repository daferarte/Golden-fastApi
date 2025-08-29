from pydantic import BaseModel
from typing import Optional

class SedeBase(BaseModel):
    nombre_sede: Optional[str] = None
    direccion: Optional[str] = None

class SedeCreate(SedeBase):
    nombre_sede: str
    direccion: str

class SedeUpdate(SedeBase):
    pass  # Todos los campos opcionales para actualización

class SedeResponse(SedeBase):
    id: int

    class Config:
        orm_mode = True

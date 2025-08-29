from pydantic import BaseModel
from datetime import date

class VentaMembresiaBase(BaseModel):
    id_cliente: int
    id_membresia: int
    fecha_inicio: date
    fecha_fin: date
    precio_final: float
    estado: str
    sesiones_restantes: int

class VentaMembresiaCreate(VentaMembresiaBase):
    pass

class VentaMembresiaUpdate(VentaMembresiaBase):
    pass

class VentaMembresiaResponse(VentaMembresiaBase):
    id: int
    class Config:
        orm_mode = True

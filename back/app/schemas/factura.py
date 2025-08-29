from pydantic import BaseModel
from datetime import date

class FacturaBase(BaseModel):
    numero_factura: str
    fecha_emision: date
    id_cliente: int
    subtotal: float
    descuento_total: float
    total: float
    metodo_pago: str
    estado: str

class FacturaCreate(FacturaBase):
    pass

class FacturaUpdate(FacturaBase):
    pass

class FacturaResponse(FacturaBase):
    id: int
    class Config:
        orm_mode = True


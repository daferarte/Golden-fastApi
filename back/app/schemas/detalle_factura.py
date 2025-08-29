from pydantic import BaseModel

class DetalleFacturaBase(BaseModel):
    id_factura: int
    id_venta: int
    descripcion: str
    cantidad: int
    precio_unitario: float
    descuento_aplicado: float
    total_linea: float

class DetalleFacturaCreate(DetalleFacturaBase):
    pass

class DetalleFacturaUpdate(DetalleFacturaBase):
    pass

class DetalleFacturaResponse(DetalleFacturaBase):
    id: int
    class Config:
        orm_mode = True

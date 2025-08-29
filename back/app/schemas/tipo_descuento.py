from pydantic import BaseModel

class TipoDescuentoBase(BaseModel):
    nombre_descuento: str
    porcentaje_descuento: float

class TipoDescuentoCreate(TipoDescuentoBase):
    pass

class TipoDescuentoUpdate(TipoDescuentoBase):
    pass

class TipoDescuentoResponse(TipoDescuentoBase):
    id: int
    class Config:
        orm_mode = True

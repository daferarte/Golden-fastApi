from pydantic import BaseModel
from datetime import datetime

class AsistenciaBase(BaseModel):
    id_cliente: int
    id_venta: int
    id_sede: int
    fecha_hora_entrada: datetime
    tipo_acceso: str

class AsistenciaCreate(AsistenciaBase):
    pass

class AsistenciaUpdate(AsistenciaBase):
    pass

class AsistenciaResponse(AsistenciaBase):
    id: int
    class Config:
        orm_mode = True

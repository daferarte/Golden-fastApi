from pydantic import BaseModel
from typing import Optional
from datetime import date

class ReporteAsistenciaBase(BaseModel):
    id_cliente: Optional[int]
    id_sede: Optional[int]
    fecha_generacion: date
    tipo_reporte: str
    contenido: str
    enviado: bool
    fecha_envio: Optional[date]

class ReporteAsistenciaCreate(ReporteAsistenciaBase):
    pass

class ReporteAsistenciaUpdate(ReporteAsistenciaBase):
    pass

class ReporteAsistenciaResponse(ReporteAsistenciaBase):
    id: int
    class Config:
        orm_mode = True

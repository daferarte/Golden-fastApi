from pydantic import BaseModel, ConfigDict
from typing import Optional
from datetime import datetime, date

# --------- Briefs anidados ---------
class ClienteBrief(BaseModel):
    id: int
    documento: str
    nombre: str
    apellido: str
    fotografia: Optional[str] = None

    model_config = ConfigDict(from_attributes=True)


class VentaMembresiaBrief(BaseModel):
    id: int
    fecha_inicio: Optional[date] = None
    fecha_fin: Optional[date] = None
    estado: Optional[str] = None
    sesiones_restantes: Optional[int] = None

    model_config = ConfigDict(from_attributes=True)


# --------- Base / Create / Update ---------
class AsistenciaBase(BaseModel):
    id_cliente: int
    id_venta: Optional[int] = None
    id_sede: int
    fecha_hora_entrada: datetime
    tipo_acceso: str
    motivo_error: Optional[str] = None  # 🔹 NUEVO CAMPO

    # Este modelo se usa tanto en creación como en respuesta


class AsistenciaCreate(AsistenciaBase):
    pass


class AsistenciaUpdate(AsistenciaBase):
    pass


# --------- OUT con referencias ---------
class AsistenciaResponse(AsistenciaBase):
    id: int
    cliente: Optional[ClienteBrief] = None
    venta: Optional[VentaMembresiaBrief] = None

    model_config = ConfigDict(from_attributes=True)

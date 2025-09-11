from datetime import date
from typing import Optional
from pydantic import BaseModel, ConfigDict

class ResumenMembresia(BaseModel):
    # Datos del cliente
    id: int
    foto: Optional[str] = None
    documento: str
    nombre: str
    apellido: str

    # Datos de la última venta de membresía (si existe)
    id_venta: Optional[int] = None
    fecha_inicio: Optional[date] = None
    fecha_fin: Optional[date] = None
    precio: Optional[float] = None
    sesiones_restantes: Optional[int] = None
    estado: str  # "activa" | "vencida" | "sin_membresia" (o el valor de DB)

    model_config = ConfigDict(from_attributes=True)

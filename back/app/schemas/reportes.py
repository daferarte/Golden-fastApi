# app/schemas/reportes.py
from pydantic import BaseModel
from typing import List

class ResumenMembresiasOut(BaseModel):
    total_clientes: int
    activos: int
    proximos_vencer: int
    vencidos: int

class ResumenAsistenciasOut(BaseModel):
    diarias_hoy: int
    mensuales_actual: int
    anuales_actual: int

class PuntoDia(BaseModel):
    fecha: str
    total: int

class PuntoMes(BaseModel):
    anio: int
    mes: int
    total: int

class PuntoAnio(BaseModel):
    anio: int
    total: int

class SerieDiariaOut(BaseModel):
    items: List[PuntoDia]

class SerieMensualOut(BaseModel):
    items: List[PuntoMes]

class SerieAnualOut(BaseModel):
    items: List[PuntoAnio]
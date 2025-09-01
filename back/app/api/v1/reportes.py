# app/api/v1/endpoints/reportes.py
from fastapi import APIRouter, Depends, Query
from sqlalchemy.orm import Session
from app.db.session import get_db
from app.services.reportes_service import ReportesService
from app.schemas.reportes import (
    ResumenMembresiasOut, ResumenAsistenciasOut, SerieDiariaOut, SerieMensualOut, SerieAnualOut
)

router = APIRouter(prefix="/reportes", tags=["reportes"])
svc = ReportesService()

@router.get("/membresias/resumen", response_model=ResumenMembresiasOut)
def resumen_membresias(dias_alerta: int = 5, db: Session = Depends(get_db)):
    """
    Devuelve conteos de clientes por estado de su última membresía:
    activos, próximos a vencer (< dias_alerta), y vencidos.
    """
    data = svc.resumen_membresias(db, dias_alerta=dias_alerta)
    return ResumenMembresiasOut(**data)

@router.get("/asistencias/resumen", response_model=ResumenAsistenciasOut)
def resumen_asistencias(db: Session = Depends(get_db)):
    return ResumenAsistenciasOut(**svc.resumen_asistencias(db))

@router.get("/asistencias/diarias", response_model=SerieDiariaOut)
def asistencias_diarias(dias: int = Query(30, ge=1, le=365), db: Session = Depends(get_db)):
    items = svc.serie_asistencias_diarias(db, dias=dias)
    return SerieDiariaOut(items=items)

@router.get("/asistencias/mensuales", response_model=SerieMensualOut)
def asistencias_mensuales(meses: int = Query(12, ge=1, le=120), db: Session = Depends(get_db)):
    items = svc.serie_asistencias_mensuales(db, meses=meses)
    return SerieMensualOut(items=items)

@router.get("/asistencias/anuales", response_model=SerieAnualOut)
def asistencias_anuales(anios: int = Query(5, ge=1, le=50), db: Session = Depends(get_db)):
    items = svc.serie_asistencias_anuales(db, anios=anios)
    return SerieAnualOut(items=items)
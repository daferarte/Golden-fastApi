from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from app.db.session import get_db
from app.services.reporte_asistencia_service import ReporteAsistenciaService
from app.schemas.reporte_asistencia import ReporteAsistenciaCreate, ReporteAsistenciaUpdate, ReporteAsistenciaResponse
from app.api import deps

router = APIRouter()
service = ReporteAsistenciaService()

permitir_staff = deps.get_current_active_user
permitir_solo_duenos = deps.RoleChecker(["dueño"])

@router.post("/", response_model=ReporteAsistenciaResponse, dependencies=[Depends(permitir_staff)])
def create_reporte(data: ReporteAsistenciaCreate, db: Session = Depends(get_db)):
    return service.create(db, data)

@router.get("/", response_model=list[ReporteAsistenciaResponse], dependencies=[Depends(permitir_staff)])
def list_reportes(db: Session = Depends(get_db)):
    return service.get_all(db)

@router.get("/{reporte_id}", response_model=ReporteAsistenciaResponse, dependencies=[Depends(permitir_staff)])
def get_reporte(reporte_id: int, db: Session = Depends(get_db)):
    reporte = service.get_by_id(db, reporte_id)
    if not reporte:
        raise HTTPException(status_code=404, detail="Reporte de asistencia no encontrado")
    return reporte

@router.put("/{reporte_id}", response_model=ReporteAsistenciaResponse, dependencies=[Depends(permitir_solo_duenos)])
def update_reporte(reporte_id: int, data: ReporteAsistenciaUpdate, db: Session = Depends(get_db)):
    updated = service.update(db, reporte_id, data)
    if not updated:
        raise HTTPException(status_code=404, detail="Reporte de asistencia no encontrado")
    return updated

@router.delete("/{reporte_id}", dependencies=[Depends(permitir_solo_duenos)])
def delete_reporte(reporte_id: int, db: Session = Depends(get_db)):
    deleted = service.delete(db, reporte_id)
    if not deleted:
        raise HTTPException(status_code=404, detail="Reporte de asistencia no encontrado")
    return {"message": "Reporte de asistencia eliminado correctamente"}

from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from app.db.session import get_db
from app.services.asistencia_service import AsistenciaService
from app.schemas.asistencia import AsistenciaCreate, AsistenciaUpdate, AsistenciaResponse
from app.api import deps

router = APIRouter()
service = AsistenciaService()

permitir_staff = deps.get_current_active_user
permitir_solo_duenos = deps.RoleChecker(["dueño"])

@router.post("/", response_model=AsistenciaResponse, dependencies=[Depends(permitir_staff)])
def create_asistencia(data: AsistenciaCreate, db: Session = Depends(get_db)):
    return service.create(db, data)

@router.get("/", response_model=list[AsistenciaResponse], dependencies=[Depends(permitir_staff)])
def list_asistencias(db: Session = Depends(get_db)):
    return service.get_all(db)

@router.get("/{asistencia_id}", response_model=AsistenciaResponse, dependencies=[Depends(permitir_staff)])
def get_asistencia(asistencia_id: int, db: Session = Depends(get_db)):
    asistencia = service.get_by_id(db, asistencia_id)
    if not asistencia:
        raise HTTPException(status_code=404, detail="Asistencia no encontrada")
    return asistencia

@router.put("/{asistencia_id}", response_model=AsistenciaResponse, dependencies=[Depends(permitir_solo_duenos)])
def update_asistencia(asistencia_id: int, data: AsistenciaUpdate, db: Session = Depends(get_db)):
    updated = service.update(db, asistencia_id, data)
    if not updated:
        raise HTTPException(status_code=404, detail="Asistencia no encontrada")
    return updated

@router.delete("/{asistencia_id}", dependencies=[Depends(permitir_solo_duenos)])
def delete_asistencia(asistencia_id: int, db: Session = Depends(get_db)):
    deleted = service.delete(db, asistencia_id)
    if not deleted:
        raise HTTPException(status_code=404, detail="Asistencia no encontrada")
    return {"message": "Asistencia eliminada correctamente"}

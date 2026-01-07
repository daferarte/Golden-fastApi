from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from app.db.session import get_db
from app.services.sede_service import SedeService
from app.schemas.sede import SedeCreate, SedeUpdate, SedeResponse
from app.api import deps

router = APIRouter()
service = SedeService()

permitir_solo_duenos = deps.RoleChecker(["dueño"])
permitir_staff = deps.get_current_active_user

@router.post("/", response_model=SedeResponse, dependencies=[Depends(permitir_solo_duenos)])
def create_sede(data: SedeCreate, db: Session = Depends(get_db)):
    return service.create(db, data)

@router.get("/", response_model=list[SedeResponse], dependencies=[Depends(permitir_staff)])
def list_sedes(db: Session = Depends(get_db)):
    return service.get_all(db)

@router.get("/{sede_id}", response_model=SedeResponse, dependencies=[Depends(permitir_staff)])
def get_sede(sede_id: int, db: Session = Depends(get_db)):
    sede = service.get_by_id(db, sede_id)
    if not sede:
        raise HTTPException(status_code=404, detail="Sede no encontrada")
    return sede

@router.put("/{sede_id}", response_model=SedeResponse, dependencies=[Depends(permitir_solo_duenos)])
def update_sede(sede_id: int, data: SedeUpdate, db: Session = Depends(get_db)):
    updated = service.update(db, sede_id, data)
    if not updated:
        raise HTTPException(status_code=404, detail="Sede no encontrada")
    return updated

@router.delete("/{sede_id}", dependencies=[Depends(permitir_solo_duenos)])
def delete_sede(sede_id: int, db: Session = Depends(get_db)):
    deleted = service.delete(db, sede_id)
    if not deleted:
        raise HTTPException(status_code=404, detail="Sede no encontrada")
    return {"message": "Sede eliminada correctamente"}

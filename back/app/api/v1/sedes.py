from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from app.db.session import get_db
from app.services.sede_service import SedeService
from app.schemas.sede import SedeCreate, SedeUpdate, SedeResponse

router = APIRouter()
service = SedeService()

@router.post("/", response_model=SedeResponse)
def create_sede(data: SedeCreate, db: Session = Depends(get_db)):
    return service.create(db, data)

@router.get("/", response_model=list[SedeResponse])
def list_sedes(db: Session = Depends(get_db)):
    return service.get_all(db)

@router.get("/{sede_id}", response_model=SedeResponse)
def get_sede(sede_id: int, db: Session = Depends(get_db)):
    sede = service.get_by_id(db, sede_id)
    if not sede:
        raise HTTPException(status_code=404, detail="Sede no encontrada")
    return sede

@router.put("/{sede_id}", response_model=SedeResponse)
def update_sede(sede_id: int, data: SedeUpdate, db: Session = Depends(get_db)):
    updated = service.update(db, sede_id, data)
    if not updated:
        raise HTTPException(status_code=404, detail="Sede no encontrada")
    return updated

@router.delete("/{sede_id}")
def delete_sede(sede_id: int, db: Session = Depends(get_db)):
    deleted = service.delete(db, sede_id)
    if not deleted:
        raise HTTPException(status_code=404, detail="Sede no encontrada")
    return {"message": "Sede eliminada correctamente"}

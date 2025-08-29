from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from app.db.session import get_db
from app.services.membresia_service import MembresiaService
from app.schemas.membresia import MembresiaCreate, MembresiaUpdate, MembresiaResponse

router = APIRouter()
service = MembresiaService()

@router.post("/", response_model=MembresiaResponse)
def create_membresia(data: MembresiaCreate, db: Session = Depends(get_db)):
    return service.create(db, data)

@router.get("/", response_model=list[MembresiaResponse])
def list_membresias(db: Session = Depends(get_db)):
    return service.get_all(db)

@router.get("/{membresia_id}", response_model=MembresiaResponse)
def get_membresia(membresia_id: int, db: Session = Depends(get_db)):
    item = service.get_by_id(db, membresia_id)
    if not item:
        raise HTTPException(status_code=404, detail="Membresía no encontrada")
    return item

@router.put("/{membresia_id}", response_model=MembresiaResponse)
def update_membresia(membresia_id: int, data: MembresiaUpdate, db: Session = Depends(get_db)):
    updated = service.update(db, membresia_id, data)
    if not updated:
        raise HTTPException(status_code=404, detail="Membresía no encontrada")
    return updated

@router.delete("/{membresia_id}")
def delete_membresia(membresia_id: int, db: Session = Depends(get_db)):
    deleted = service.delete(db, membresia_id)
    if not deleted:
        raise HTTPException(status_code=404, detail="Membresía no encontrada")
    return {"message": "Membresía eliminada correctamente"}

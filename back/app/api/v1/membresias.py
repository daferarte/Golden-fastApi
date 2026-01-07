from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from app.db.session import get_db
from app.services.membresia_service import MembresiaService
from app.schemas.membresia import MembresiaCreate, MembresiaUpdate, MembresiaResponse
from app.api import deps

router = APIRouter()
service = MembresiaService()

permitir_solo_duenos = deps.RoleChecker(["dueño"])
permitir_staff = deps.get_current_active_user

@router.post("/", response_model=MembresiaResponse, dependencies=[Depends(permitir_solo_duenos)])
def create_membresia(data: MembresiaCreate, db: Session = Depends(get_db)):
    return service.create(db, data)

@router.get("/", response_model=list[MembresiaResponse], dependencies=[Depends(permitir_staff)])
def list_membresias(db: Session = Depends(get_db)):
    return service.get_all(db)

@router.get("/{membresia_id}", response_model=MembresiaResponse, dependencies=[Depends(permitir_staff)])
def get_membresia(membresia_id: int, db: Session = Depends(get_db)):
    item = service.get_by_id(db, membresia_id)
    if not item:
        raise HTTPException(status_code=404, detail="Membresía no encontrada")
    return item

@router.put("/{membresia_id}", response_model=MembresiaResponse, dependencies=[Depends(permitir_solo_duenos)])
def update_membresia(membresia_id: int, data: MembresiaUpdate, db: Session = Depends(get_db)):
    updated = service.update(db, membresia_id, data)
    if not updated:
        raise HTTPException(status_code=404, detail="Membresía no encontrada")
    return updated

@router.delete("/{membresia_id}", dependencies=[Depends(permitir_solo_duenos)])
def delete_membresia(membresia_id: int, db: Session = Depends(get_db)):
    deleted = service.delete(db, membresia_id)
    if not deleted:
        raise HTTPException(status_code=404, detail="Membresía no encontrada")
    return {"message": "Membresía eliminada correctamente"}

from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from app.db.session import get_db
from app.services.rol_service import RolService
from app.schemas.rol import RolCreate, RolUpdate, RolResponse

router = APIRouter()
service = RolService()

@router.post("/", response_model=RolResponse)
def create_rol(data: RolCreate, db: Session = Depends(get_db)):
    return service.create(db, data)

@router.get("/", response_model=list[RolResponse])
def list_roles(db: Session = Depends(get_db)):
    return service.get_all(db)

@router.get("/{rol_id}", response_model=RolResponse)
def get_rol(rol_id: int, db: Session = Depends(get_db)):
    rol = service.get_by_id(db, rol_id)
    if not rol:
        raise HTTPException(status_code=404, detail="Rol no encontrado")
    return rol

@router.put("/{rol_id}", response_model=RolResponse)
def update_rol(rol_id: int, data: RolUpdate, db: Session = Depends(get_db)):
    updated = service.update(db, rol_id, data)
    if not updated:
        raise HTTPException(status_code=404, detail="Rol no encontrado")
    return updated

@router.delete("/{rol_id}")
def delete_rol(rol_id: int, db: Session = Depends(get_db)):
    deleted = service.delete(db, rol_id)
    if not deleted:
        raise HTTPException(status_code=404, detail="Rol no encontrado")
    return {"message": "Rol eliminado correctamente"}

from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from app.db.session import get_db
from app.services.venta_membresia_service import VentaMembresiaService
from app.schemas.venta_membresia import VentaMembresiaCreate, VentaMembresiaUpdate, VentaMembresiaResponse
from app.api import deps

router = APIRouter()
service = VentaMembresiaService()

permitir_solo_duenos = deps.RoleChecker(["dueño"])
permitir_staff = deps.get_current_active_user

@router.post("/", response_model=VentaMembresiaResponse, dependencies=[Depends(permitir_staff)])
def create_venta(data: VentaMembresiaCreate, db: Session = Depends(get_db)):
    return service.create(db, data)

@router.get("/", response_model=list[VentaMembresiaResponse], dependencies=[Depends(permitir_staff)])
def list_ventas(db: Session = Depends(get_db)):
    return service.get_all(db)

@router.get("/{venta_id}", response_model=VentaMembresiaResponse, dependencies=[Depends(permitir_staff)])
def get_venta(venta_id: int, db: Session = Depends(get_db)):
    venta = service.get_by_id(db, venta_id)
    if not venta:
        raise HTTPException(status_code=404, detail="Venta no encontrada")
    return venta

@router.put("/{venta_id}", response_model=VentaMembresiaResponse, dependencies=[Depends(permitir_solo_duenos)])
def update_venta(venta_id: int, data: VentaMembresiaUpdate, db: Session = Depends(get_db)):
    updated = service.update(db, venta_id, data)
    if not updated:
        raise HTTPException(status_code=404, detail="Venta no encontrada")
    return updated

@router.delete("/{venta_id}", dependencies=[Depends(permitir_solo_duenos)])
def delete_venta(venta_id: int, db: Session = Depends(get_db)):
    deleted = service.delete(db, venta_id)
    if not deleted:
        raise HTTPException(status_code=404, detail="Venta no encontrada")
    return {"message": "Venta eliminada correctamente"}

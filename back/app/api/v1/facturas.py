from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from app.db.session import get_db
from app.services.factura_service import FacturaService
from app.schemas.factura import FacturaCreate, FacturaUpdate, FacturaResponse
from app.api import deps

router = APIRouter()
service = FacturaService()

permitir_staff = deps.get_current_active_user
permitir_solo_duenos = deps.RoleChecker(["dueño"])

@router.post("/", response_model=FacturaResponse, dependencies=[Depends(permitir_staff)])
def create_factura(data: FacturaCreate, db: Session = Depends(get_db)):
    return service.create(db, data)

@router.get("/", response_model=list[FacturaResponse], dependencies=[Depends(permitir_staff)])
def list_facturas(db: Session = Depends(get_db)):
    return service.get_all(db)

@router.get("/{factura_id}", response_model=FacturaResponse, dependencies=[Depends(permitir_staff)])
def get_factura(factura_id: int, db: Session = Depends(get_db)):
    factura = service.get_by_id(db, factura_id)
    if not factura:
        raise HTTPException(status_code=404, detail="Factura no encontrada")
    return factura

@router.put("/{factura_id}", response_model=FacturaResponse, dependencies=[Depends(permitir_solo_duenos)])
def update_factura(factura_id: int, data: FacturaUpdate, db: Session = Depends(get_db)):
    updated = service.update(db, factura_id, data)
    if not updated:
        raise HTTPException(status_code=404, detail="Factura no encontrada")
    return updated

@router.delete("/{factura_id}", dependencies=[Depends(permitir_solo_duenos)])
def delete_factura(factura_id: int, db: Session = Depends(get_db)):
    deleted = service.delete(db, factura_id)
    if not deleted:
        raise HTTPException(status_code=404, detail="Factura no encontrada")
    return {"message": "Factura eliminada correctamente"}

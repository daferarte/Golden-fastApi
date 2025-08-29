from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from app.db.session import get_db
from app.services.factura_service import FacturaService
from app.schemas.factura import FacturaCreate, FacturaUpdate, FacturaResponse

router = APIRouter()
service = FacturaService()

@router.post("/", response_model=FacturaResponse)
def create_factura(data: FacturaCreate, db: Session = Depends(get_db)):
    return service.create(db, data)

@router.get("/", response_model=list[FacturaResponse])
def list_facturas(db: Session = Depends(get_db)):
    return service.get_all(db)

@router.get("/{factura_id}", response_model=FacturaResponse)
def get_factura(factura_id: int, db: Session = Depends(get_db)):
    factura = service.get_by_id(db, factura_id)
    if not factura:
        raise HTTPException(status_code=404, detail="Factura no encontrada")
    return factura

@router.put("/{factura_id}", response_model=FacturaResponse)
def update_factura(factura_id: int, data: FacturaUpdate, db: Session = Depends(get_db)):
    updated = service.update(db, factura_id, data)
    if not updated:
        raise HTTPException(status_code=404, detail="Factura no encontrada")
    return updated

@router.delete("/{factura_id}")
def delete_factura(factura_id: int, db: Session = Depends(get_db)):
    deleted = service.delete(db, factura_id)
    if not deleted:
        raise HTTPException(status_code=404, detail="Factura no encontrada")
    return {"message": "Factura eliminada correctamente"}

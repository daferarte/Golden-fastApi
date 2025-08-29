from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from app.db.session import get_db
from app.services.detalle_factura_service import DetalleFacturaService
from app.schemas.detalle_factura import DetalleFacturaCreate, DetalleFacturaUpdate, DetalleFacturaResponse

router = APIRouter()
service = DetalleFacturaService()

@router.post("/", response_model=DetalleFacturaResponse)
def create_detalle(data: DetalleFacturaCreate, db: Session = Depends(get_db)):
    return service.create(db, data)

@router.get("/", response_model=list[DetalleFacturaResponse])
def list_detalles(db: Session = Depends(get_db)):
    return service.get_all(db)

@router.get("/{detalle_id}", response_model=DetalleFacturaResponse)
def get_detalle(detalle_id: int, db: Session = Depends(get_db)):
    detalle = service.get_by_id(db, detalle_id)
    if not detalle:
        raise HTTPException(status_code=404, detail="Detalle de factura no encontrado")
    return detalle

@router.put("/{detalle_id}", response_model=DetalleFacturaResponse)
def update_detalle(detalle_id: int, data: DetalleFacturaUpdate, db: Session = Depends(get_db)):
    updated = service.update(db, detalle_id, data)
    if not updated:
        raise HTTPException(status_code=404, detail="Detalle de factura no encontrado")
    return updated

@router.delete("/{detalle_id}")
def delete_detalle(detalle_id: int, db: Session = Depends(get_db)):
    deleted = service.delete(db, detalle_id)
    if not deleted:
        raise HTTPException(status_code=404, detail="Detalle de factura no encontrado")
    return {"message": "Detalle de factura eliminado correctamente"}

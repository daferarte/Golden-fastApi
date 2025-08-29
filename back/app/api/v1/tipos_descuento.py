from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from app.db.session import get_db
from app.services.tipo_descuento_service import TipoDescuentoService
from app.schemas.tipo_descuento import TipoDescuentoCreate, TipoDescuentoUpdate, TipoDescuentoResponse

router = APIRouter()
service = TipoDescuentoService()

@router.post("/", response_model=TipoDescuentoResponse)
def create_tipo_descuento(data: TipoDescuentoCreate, db: Session = Depends(get_db)):
    return service.create(db, data)

@router.get("/", response_model=list[TipoDescuentoResponse])
def list_tipos_descuento(db: Session = Depends(get_db)):
    return service.get_all(db)

@router.get("/{tipo_id}", response_model=TipoDescuentoResponse)
def get_tipo_descuento(tipo_id: int, db: Session = Depends(get_db)):
    tipo = service.get_by_id(db, tipo_id)
    if not tipo:
        raise HTTPException(status_code=404, detail="Tipo de descuento no encontrado")
    return tipo

@router.put("/{tipo_id}", response_model=TipoDescuentoResponse)
def update_tipo_descuento(tipo_id: int, data: TipoDescuentoUpdate, db: Session = Depends(get_db)):
    updated = service.update(db, tipo_id, data)
    if not updated:
        raise HTTPException(status_code=404, detail="Tipo de descuento no encontrado")
    return updated

@router.delete("/{tipo_id}")
def delete_tipo_descuento(tipo_id: int, db: Session = Depends(get_db)):
    deleted = service.delete(db, tipo_id)
    if not deleted:
        raise HTTPException(status_code=404, detail="Tipo de descuento no encontrado")
    return {"message": "Tipo de descuento eliminado correctamente"}

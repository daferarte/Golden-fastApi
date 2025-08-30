from fastapi import APIRouter, Depends, HTTPException, Query, Request
from sqlalchemy.orm import Session
from app.db.session import get_db
from app.services.cliente_service import ClienteService
from app.schemas.cliente import ClienteCreate, ClienteCreateRequest, ClienteUpdate, ClienteResponse
from pydantic import BaseModel
import base64
import binascii
from app.repositories.cliente_repository import ClienteRepository
from typing import Optional, Dict
from app.schemas.common import Page
from app.schemas.membresia_resumen import ResumenMembresia

from app.schemas.cliente_membresia import (
    CrearClienteYVentaRequest,
    CrearClienteYVentaResponse,
    ActualizarClienteYVentaRequest
)
from app.services.cliente_membresia_service import crear_cliente_y_venta, update_cliente_y_venta


router = APIRouter()
service = ClienteService()

# Campos permitidos para ordenamiento (clave pública -> atributo en el modelo)
SORT_FIELDS: Dict[str, str] = {
    "id": "id",
    "nombre": "nombre",
    "apellido": "apellido",
    "documento": "documento",
    "correo": "correo",
    "fecha_nacimiento": "fecha_nacimiento",
}

class HuellaRequest(BaseModel):
    huella_base64: str


@router.post("/", response_model=ClienteResponse)
def create_cliente(data: ClienteCreateRequest, db: Session = Depends(get_db)):
    huella_bytes = None
    if data.huella_template:
        try:
            huella_bytes = base64.b64decode(data.huella_template)
        except (binascii.Error, TypeError):
            raise HTTPException(
                status_code=400,
                detail="El formato de la huella en Base64 es inválido."
            )
    cliente_data = data.dict(exclude={"huella_template"})
    cliente_data["huella_template"] = huella_bytes
    cliente_a_crear = ClienteCreate(**cliente_data)
    return service.create(db, cliente_a_crear)


@router.get("/", response_model=Page[ClienteResponse])
def list_clientes(
    request: Request,
    db: Session = Depends(get_db),
    page: int = Query(1, ge=1, description="Número de página (1..N)"),
    size: int = Query(20, ge=1, le=200, description="Tamaño de página"),
    q: Optional[str] = Query(None, description="Búsqueda por nombre, apellido, documento o correo"),
    sort: str = Query("nombre", description=f"Campo de orden: {', '.join(SORT_FIELDS.keys())}"),
    order: str = Query("asc", pattern="^(asc|desc)$", description="asc|desc"),
    ):
    if sort not in SORT_FIELDS:
        raise HTTPException(status_code=400, detail=f"Campo sort inválido. Usa: {', '.join(SORT_FIELDS)}")

    total, items, pages, page = service.get_paginated(
        db=db,
        page=page,
        size=size,
        q=q,
        sort_attr=SORT_FIELDS[sort],
        descending=(order == "desc"),
    )

    def link_for(p: int) -> Optional[str]:
        if p < 1 or (total and p > pages):
            return None
        return str(request.url.include_query_params(page=p, size=size, q=q, sort=sort, order=order))

    return Page[ClienteResponse](
        items=items,
        page=page,
        size=size,
        total=total,
        pages=pages,
        has_next=page < pages,
        has_prev=page > 1,
        next=link_for(page + 1) if page < pages else None,
        prev=link_for(page - 1) if page > 1 else None,
    )


@router.get("/{cliente_id}", response_model=ClienteResponse)
def get_cliente(cliente_id: int, db: Session = Depends(get_db)):
    cliente = service.get_by_id(db, cliente_id)
    if not cliente:
        raise HTTPException(status_code=404, detail="Cliente no encontrado")
    return cliente

@router.put("/{cliente_id}", response_model=ClienteResponse)
def update_cliente(cliente_id: int, data: ClienteUpdate, db: Session = Depends(get_db)):
    updated = service.update(db, cliente_id, data)
    if not updated:
        raise HTTPException(status_code=404, detail="Cliente no encontrado")
    return updated

@router.delete("/{cliente_id}")
def delete_cliente(cliente_id: int, db: Session = Depends(get_db)):
    deleted = service.delete(db, cliente_id)
    if not deleted:
        raise HTTPException(status_code=404, detail="Cliente no encontrado")
    return {"message": "Cliente eliminado correctamente"}

# --- Endpoint de Actualización de Huella Ajustado ---
@router.put("/{cliente_id}/huella", response_model=ClienteResponse)
def actualizar_huella_cliente(cliente_id: int, request: HuellaRequest, db: Session = Depends(get_db)):
    """
    Actualiza la plantilla de la huella para un cliente existente.
    """
    try:
        huella_bytes = base64.b64decode(request.huella_base64)
    except Exception:
        raise HTTPException(status_code=400, detail="Formato de huella Base64 inválido.")
    
    # Llama al método 'update_huella' del servicio que tienes en el otro Canvas
    cliente_actualizado = service.update_huella(db, cliente_id, huella_bytes)
    
    if not cliente_actualizado:
        raise HTTPException(status_code=404, detail="Cliente no encontrado")
        
    return cliente_actualizado

@router.get("/by-huella/{id_huella}", response_model=ClienteResponse)
def get_cliente_by_huella(id_huella: int, db: Session = Depends(get_db)):
    """
    Busca y devuelve los datos de un cliente usando su id_huella.
    Este es el endpoint que debe llamar la función 'identificarUsuario' del ESP32.
    """
    repo = ClienteRepository() 
    cliente = repo.get_by_id_huella(db, id_huella=id_huella)
    
    if not cliente:
        raise HTTPException(status_code=404, detail="Cliente con esa huella no fue encontrado")
    return cliente

@router.get("/{cliente_id}/membresia-actual", response_model=ResumenMembresia)
def obtener_membresia_actual(cliente_id: int, db: Session = Depends(get_db)):
    """
    Última venta de membresía para un cliente: foto, nombre, apellido,
    fecha_inicio, fecha_fin, precio, sesiones_restantes, estado.
    """
    resumen = service.get_membership_summary(db, cliente_id)
    if not resumen:
        raise HTTPException(status_code=404, detail="Cliente sin membresía registrada")
    return resumen

@router.get("/membresias/resumen", response_model=Page[ResumenMembresia])
def listar_resumen_membresias(
    request: Request,
    db: Session = Depends(get_db),
    page: int = Query(1, ge=1),
    size: int = Query(20, ge=1, le=200),
    q: Optional[str] = Query(None, description="Buscar por nombre, documento o correo"),
):
    """
    Lista paginada: por cada cliente, su última venta de membresía (si existe).
    """
    total, items = service.list_membership_summaries(db, page=page, size=size, q=q)
    pages = (total + size - 1) // size if total else 1

    def link_for(p: int) -> Optional[str]:
        if p < 1 or (total and p > pages):
            return None
        return str(request.url.include_query_params(page=p, size=size, q=q))

    return {
        "items": items,
        "page": page,
        "size": size,
        "total": total,
        "pages": pages,
        "has_next": page < pages,
        "has_prev": page > 1,
        "next": link_for(page + 1) if page < pages else None,
        "prev": link_for(page - 1) if page > 1 else None,
    }
    
@router.post("/with-membresia", response_model=CrearClienteYVentaResponse, status_code=201)
def crear_cliente_con_membresia(payload: CrearClienteYVentaRequest, db: Session = Depends(get_db)):
    return crear_cliente_y_venta(db, payload)

@router.put("/clientes/{cliente_id}/with-membresia", response_model=CrearClienteYVentaResponse,
    summary="Actualiza datos del cliente y su venta de membresía (parcial)",
)
def actualizar_cliente_con_membresia(cliente_id: int, payload: ActualizarClienteYVentaRequest, db: Session = Depends(get_db),):
    """
    - Si `venta.id` viene, se actualiza esa venta del cliente.
    - Si **no** viene `venta.id`, se toma la venta **más reciente** del cliente (por `fecha_inicio`).
    - Si el cliente **no tiene ventas** y el payload trae datos de venta, se crea **una nueva** (requiere `id_membresia`).
    - El update es **parcial**: sólo aplica a los campos enviados.
    """
    return update_cliente_y_venta(db, cliente_id, payload)
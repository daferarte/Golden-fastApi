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
from app.api import deps

# ⬇️ NUEVOS IMPORTS para el resumen con filtros
from sqlalchemy import func, case, and_, or_
from app.models.cliente import Cliente
from app.models.venta_membresia import VentaMembresia

from app.schemas.cliente_membresia import (
    CrearClienteYVentaRequest,
    CrearClienteYVentaResponse,
    ActualizarClienteYVentaRequest
)
from app.services.cliente_membresia_service import crear_cliente_y_venta, update_cliente_y_venta


router = APIRouter()
service = ClienteService()

# Definimos permisos (ejemplo: solo dueños/admin borran clientes)
permitir_solo_duenos = deps.RoleChecker(["dueño"])
permitir_staff = deps.get_current_active_user # Cualquier usuario logueado activo

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


@router.post("/", response_model=ClienteResponse, dependencies=[Depends(permitir_staff)])
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


@router.get("/", response_model=Page[ClienteResponse], dependencies=[Depends(permitir_staff)])
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


@router.get("/{cliente_id}", response_model=ClienteResponse, dependencies=[Depends(permitir_staff)])
def get_cliente(cliente_id: int, db: Session = Depends(get_db)):
    cliente = service.get_by_id(db, cliente_id)
    if not cliente:
        raise HTTPException(status_code=404, detail="Cliente no encontrado")
    return cliente

@router.put("/{cliente_id}", response_model=ClienteResponse, dependencies=[Depends(permitir_staff)])
def update_cliente(cliente_id: int, data: ClienteUpdate, db: Session = Depends(get_db)):
    updated = service.update(db, cliente_id, data)
    if not updated:
        raise HTTPException(status_code=404, detail="Cliente no encontrado")
    return updated

@router.delete("/{cliente_id}", dependencies=[Depends(permitir_solo_duenos)])
def delete_cliente(cliente_id: int, db: Session = Depends(get_db)):
    deleted = service.delete(db, cliente_id)
    if not deleted:
        raise HTTPException(status_code=404, detail="Cliente no encontrado")
    return {"message": "Cliente eliminado correctamente"}

# --- Endpoint de Actualización de Huella Ajustado ---
@router.put("/{cliente_id}/huella", response_model=ClienteResponse, dependencies=[Depends(permitir_staff)])
def actualizar_huella_cliente(cliente_id: int, request: HuellaRequest, db: Session = Depends(get_db)):
    """
    Actualiza la plantilla de la huella para un cliente existente.
    """
    try:
        huella_bytes = base64.b64decode(request.huella_base64)
    except Exception:
        raise HTTPException(status_code=400, detail="Formato de huella Base64 inválido.")
    
    cliente_actualizado = service.update_huella(db, cliente_id, huella_bytes)
    if not cliente_actualizado:
        raise HTTPException(status_code=404, detail="Cliente no encontrado")
    return cliente_actualizado

@router.get("/by-huella/{id_huella}", response_model=ClienteResponse, dependencies=[Depends(permitir_staff)])
def get_cliente_by_huella(id_huella: int, db: Session = Depends(get_db)):
    """
    Busca y devuelve los datos de un cliente usando su id_huella.
    """
    repo = ClienteRepository() 
    cliente = repo.get_by_id_huella(db, id_huella=id_huella)
    if not cliente:
        raise HTTPException(status_code=404, detail="Cliente con esa huella no fue encontrado")
    return cliente

@router.get("/{cliente_id}/membresia-actual", response_model=ResumenMembresia, dependencies=[Depends(permitir_staff)])
def obtener_membresia_actual(cliente_id: int, db: Session = Depends(get_db)):
    """
    Última venta de membresía para un cliente.
    """
    resumen = service.get_membership_summary(db, cliente_id)
    if not resumen:
        raise HTTPException(status_code=404, detail="Cliente sin membresía registrada")
    return resumen

# =================== RESUMEN CON FILTROS EN BACKEND ===================
@router.get("/membresias/resumen", response_model=Page[ResumenMembresia], dependencies=[Depends(permitir_staff)])
def listar_resumen_membresias(
    request: Request,
    db: Session = Depends(get_db),
    page: int = Query(1, ge=1),
    size: int = Query(20, ge=1, le=200),
    q: Optional[str] = Query(None, description="Buscar por nombre, documento o correo"),
    filtro: str = Query("todas", regex="^(todas|activas|por_vencer|vencidas)$"),
):
    """
    Lista paginada: por cada cliente, su última venta de membresía (si existe).
    Filtro en backend:
      - todas: sin filtro extra
      - activas: DATEDIFF(fecha_fin, CURDATE()) > 5 y estado != 'vencida'
      - por_vencer: 0 <= DATEDIFF(fecha_fin, CURDATE()) <= 5
      - vencidas: DATEDIFF(fecha_fin, CURDATE()) < 0  o estado = 'vencida'
    """
    c = Cliente
    vm = VentaMembresia

    # subconsulta: última venta por cliente (max fecha_inicio)
    subq = (
        db.query(
            vm.id_cliente.label("id_cliente"),
            func.max(vm.fecha_inicio).label("max_fecha"),
        )
        .group_by(vm.id_cliente)
        .subquery()
    )

    days_left = func.datediff(vm.fecha_fin, func.curdate())

    base_q = (
        db.query(
            c.id.label("id"),
            c.fotografia.label("foto"),
            c.nombre,
            c.apellido,
            c.documento,
            vm.id.label("id_venta"),
            vm.fecha_inicio,
            vm.fecha_fin,
            vm.precio_final.label("precio"),
            vm.sesiones_restantes,
            vm.estado,
            days_left.label("days_left"),
        )
        .outerjoin(subq, subq.c.id_cliente == c.id)
        .outerjoin(vm, and_(vm.id_cliente == subq.c.id_cliente, vm.fecha_inicio == subq.c.max_fecha))
    )

    # búsqueda
    if q:
        like = f"%{q.strip()}%"
        base_q = base_q.filter(
            or_(
                func.concat(c.nombre, " ", c.apellido).like(like),
                c.documento.like(like),
                c.correo.like(like),
            )
        )

    # filtros por estado/tiempo
    if filtro == "vencidas":
        base_q = base_q.filter(or_(days_left < 0, vm.estado == "vencida"))
    elif filtro == "por_vencer":
        base_q = base_q.filter(and_(days_left >= 0, days_left <= 5))
    elif filtro == "activas":
        base_q = base_q.filter(and_(days_left > 5, vm.estado != "vencida"))
    # "todas": sin filtro extra

    total = base_q.count()

    # orden: ventas nulas al final, luego por fecha_inicio desc
    base_q = base_q.order_by(vm.fecha_inicio.is_(None).asc(), vm.fecha_inicio.desc())

    # paginación
    pages = (total + size - 1) // size if total else 1
    if pages < 1:
        pages = 1
    if page > pages:
        page = pages
    offset = (page - 1) * size

    rows = base_q.offset(offset).limit(size).all()

    items = [
        {
            "id": r.id,
            "foto": r.foto,
            "nombre": r.nombre,
            "apellido": r.apellido,
            "documento": r.documento,
            "id_venta": r.id_venta,
            "fecha_inicio": r.fecha_inicio,
            "fecha_fin": r.fecha_fin,
            "precio": r.precio,
            "sesiones_restantes": r.sesiones_restantes,
            "estado": r.estado or "sin_membresia",
            # "days_left": r.days_left,  # si lo quieres en front, añade este campo al schema
        }
        for r in rows
    ]

    def link_for(p: int) -> Optional[str]:
        if p < 1 or (total and p > pages):
            return None
        return str(request.url.include_query_params(page=p, size=size, q=q, filtro=filtro))

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

# =================== CREAR / ACTUALIZAR CLIENTE+VENTA ===================

@router.post("/with-membresia", response_model=CrearClienteYVentaResponse, status_code=201, dependencies=[Depends(permitir_staff)])
def crear_cliente_con_membresia(payload: CrearClienteYVentaRequest, db: Session = Depends(get_db)):
    return crear_cliente_y_venta(db, payload)

# ⚠️ ARREGLADO: antes decía "/clientes/{cliente_id}/with-membresia" y duplicaba el prefijo
@router.put("/{cliente_id}/with-membresia",
    response_model=CrearClienteYVentaResponse,
    summary="Actualiza datos del cliente y su venta de membresía (parcial)",
    dependencies=[Depends(permitir_staff)]
)
def actualizar_cliente_con_membresia(
    cliente_id: int,
    payload: ActualizarClienteYVentaRequest,
    db: Session = Depends(get_db),
):
    """
    - Si `venta.id` viene, se actualiza esa venta del cliente.
    - Si NO viene `venta.id`, se toma la venta más reciente del cliente (por `fecha_inicio`).
    - Si el cliente no tiene ventas y el payload trae datos de venta, se crea una nueva (requiere `id_membresia`).
    - Update parcial: sólo aplica a los campos enviados.
    """
    return update_cliente_y_venta(db, cliente_id, payload)

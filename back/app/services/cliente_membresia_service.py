# app/services/cliente_membresia_service.py
import base64
from datetime import date as date_cls
from typing import Optional

from fastapi import HTTPException
from sqlalchemy.orm import Session
from sqlalchemy import select
from sqlalchemy.exc import SQLAlchemyError, IntegrityError

from app.models.cliente import Cliente
from app.models.venta_membresia import VentaMembresia
from app.models.membresia import Membresia
from app.repositories.cliente_repository import ClienteRepository
from app.schemas.cliente_membresia import (
    CrearClienteYVentaRequest, CrearClienteYVentaResponse,
    ClienteOut, VentaMembresiaOut,
    ActualizarClienteYVentaRequest,
)

repo_cliente = ClienteRepository()


# ------------------- Helpers -------------------

def _decode_b64_or_none(b64: Optional[str]) -> Optional[bytes]:
    if b64 is None:
        return None
    if b64 == "":  # semántica: cadena vacía -> limpiar
        return b""
    try:
        return base64.b64decode(b64)
    except Exception:
        raise HTTPException(status_code=400, detail="Base64 inválido en huella/fotografía.")


def _plus_one_month(d: date_cls) -> date_cls:
    # simple y seguro (evita problemas de fin de mes)
    y, m = d.year, d.month
    if m == 12:
        return date_cls(y + 1, 1, min(d.day, 28))
    return date_cls(y, m + 1, min(d.day, 28))


def _get_latest_venta(db: Session, cliente_id: int) -> Optional[VentaMembresia]:
    return (
        db.query(VentaMembresia)
        .filter(VentaMembresia.id_cliente == cliente_id)
        .order_by(VentaMembresia.fecha_inicio.desc())
        .first()
    )


def _venta_payload_has_data(v) -> bool:
    if v is None:
        return False
    return any(
        getattr(v, f, None) is not None
        for f in ("id_membresia", "fecha_inicio", "fecha_fin", "precio_final", "sesiones_restantes", "estado")
    )


# ------------------- Crear -------------------

def crear_cliente_y_venta(db: Session, payload: CrearClienteYVentaRequest) -> CrearClienteYVentaResponse:
    # 1) Validación cliente duplicado por documento
    if repo_cliente.get_by_documento(db, payload.cliente.documento):
        raise HTTPException(status_code=400, detail="Ya existe un cliente con este documento.")

    # 2) Validar que la membresía exista
    memb_id = payload.venta.id_membresia
    memb_exists = db.scalar(select(Membresia.id).where(Membresia.id == memb_id))
    if not memb_exists:
        raise HTTPException(status_code=404, detail=f"Membresía {memb_id} no existe.")

    # FOTO: guardamos RUTA (string) si llega
    fotografia_ruta: Optional[str] = payload.cliente.fotografia or None

    # HUELLA (opcional)
    huella_bytes = _decode_b64_or_none(payload.cliente.huella_base64)
    id_huella = None
    if huella_bytes:  # si llegó algo distinto de None / ""
        id_huella = repo_cliente.find_next_available_huella_id(db)

    try:
        # --- Crear cliente ---
        cliente = Cliente(
            nombre=payload.cliente.nombre,
            apellido=payload.cliente.apellido,
            documento=payload.cliente.documento,
            fecha_nacimiento=payload.cliente.fecha_nacimiento,
            correo=payload.cliente.correo,
            telefono=payload.cliente.telefono,
            direccion=payload.cliente.direccion,
            fotografia=fotografia_ruta,      # <- string ruta; comenta si tu columna es binaria
            id_tipo_descuento= payload.cliente.id_tipo_descuento,
            huella_template=huella_bytes or None,
            id_huella=id_huella,
        )
        db.add(cliente)
        db.flush()  # asigna cliente.id

        # Defaults seguros para venta
        venta_in = payload.venta
        fecha_inicio = venta_in.fecha_inicio or date_cls.today()
        fecha_fin = venta_in.fecha_fin or _plus_one_month(fecha_inicio)
        estado = (venta_in.estado or "activa").lower()
        precio_final = 0.0 if venta_in.precio_final is None else float(venta_in.precio_final)
        sesiones_restantes = 0 if venta_in.sesiones_restantes is None else int(venta_in.sesiones_restantes)

        venta = VentaMembresia(
            id_cliente=cliente.id,
            id_membresia=venta_in.id_membresia,
            fecha_inicio=fecha_inicio,
            fecha_fin=fecha_fin,
            precio_final=precio_final,
            sesiones_restantes=sesiones_restantes,
            estado=estado,
        )
        db.add(venta)
        db.flush()  # asigna venta.id

        db.commit()
        db.refresh(cliente)
        db.refresh(venta)

    except IntegrityError as e:
        db.rollback()
        msg = str(getattr(e.orig, "args", e.args))
        raise HTTPException(status_code=400, detail=f"Violación de integridad al crear cliente/venta: {msg}")
    except SQLAlchemyError as e:
        db.rollback()
        raise HTTPException(status_code=500, detail=f"SQLAlchemyError: {e}")
    except Exception as e:
        db.rollback()
        raise HTTPException(status_code=500, detail=f"Error al crear cliente y venta: {e}")

    return CrearClienteYVentaResponse(
        cliente=ClienteOut.model_validate(cliente),
        venta=VentaMembresiaOut.model_validate(venta),
    )


# ------------------- Actualizar (cliente + venta) -------------------

def update_cliente_y_venta(
    db: Session, cliente_id: int, payload: ActualizarClienteYVentaRequest
) -> CrearClienteYVentaResponse:
    cliente = db.get(Cliente, cliente_id)
    if not cliente:
        raise HTTPException(status_code=404, detail="Cliente no encontrado.")

    # Documento único si se cambia
    if getattr(payload.cliente, "documento", None) and payload.cliente.documento != cliente.documento:
        existente = repo_cliente.get_by_documento(db, payload.cliente.documento)
        if existente and existente.id != cliente.id:
            raise HTTPException(status_code=400, detail="Ya existe otro cliente con ese documento.")

    # Validar membresía si se envía (para update o creación de venta)
    if getattr(payload.venta, "id_membresia", None) is not None:
        memb_exists = db.scalar(select(Membresia.id).where(Membresia.id == payload.venta.id_membresia))
        if not memb_exists:
            raise HTTPException(status_code=404, detail=f"Membresía {payload.venta.id_membresia} no existe.")

    try:
        # ---- Actualizar CLIENTE (parcial) ----
        c = payload.cliente
        for field in ["nombre", "apellido", "documento", "fecha_nacimiento", "correo", "telefono", "direccion"]:
            val = getattr(c, field, None)
            if val is not None:
                setattr(cliente, field, val)

        # Fotografía: ruta string (si tu columna es binaria, no asignes string aquí)
        if hasattr(c, "fotografia") and c.fotografia is not None:
            cliente.fotografia = c.fotografia  # <- string ruta; comenta si tu columna es binaria

        # Huella: semántica -> si viene "", se limpia; si viene base64 válido, se asigna.
        if hasattr(c, "huella_base64") and c.huella_base64 is not None:
            huella_bytes = _decode_b64_or_none(c.huella_base64)
            if huella_bytes == b"":  # limpiar
                cliente.huella_template = None
                cliente.id_huella = None
            else:
                cliente.huella_template = huella_bytes
                if not cliente.id_huella:
                    cliente.id_huella = repo_cliente.find_next_available_huella_id(db)

        # ---- Actualizar/crear VENTA ----
        v_in = payload.venta
        venta_obj: Optional[VentaMembresia] = None

        if getattr(v_in, "id", None):
            venta_obj = db.get(VentaMembresia, v_in.id)
            if not venta_obj or venta_obj.id_cliente != cliente.id:
                raise HTTPException(status_code=404, detail="Venta de membresía no encontrada para este cliente.")
        else:
            venta_obj = _get_latest_venta(db, cliente.id)

        if not venta_obj and _venta_payload_has_data(v_in):
            # crear nueva (requiere id_membresia)
            if v_in.id_membresia is None:
                raise HTTPException(status_code=400, detail="Para crear una venta nueva, id_membresia es obligatorio.")
            venta_obj = VentaMembresia(
                id_cliente=cliente.id,
                id_membresia=v_in.id_membresia,
                fecha_inicio=v_in.fecha_inicio or date_cls.today(),
                fecha_fin=v_in.fecha_fin,
                precio_final=0.0 if v_in.precio_final is None else float(v_in.precio_final),
                sesiones_restantes=0 if v_in.sesiones_restantes is None else int(v_in.sesiones_restantes),
                estado=(v_in.estado or "activa").lower(),
            )
            db.add(venta_obj)
            db.flush()
        elif venta_obj:
            # update parcial
            if v_in.id_membresia is not None:
                venta_obj.id_membresia = v_in.id_membresia
            if v_in.fecha_inicio is not None:
                venta_obj.fecha_inicio = v_in.fecha_inicio
            if v_in.fecha_fin is not None:
                venta_obj.fecha_fin = v_in.fecha_fin
            if v_in.precio_final is not None:
                venta_obj.precio_final = float(v_in.precio_final)
            if v_in.sesiones_restantes is not None:
                venta_obj.sesiones_restantes = int(v_in.sesiones_restantes)
            if v_in.estado is not None:
                venta_obj.estado = v_in.estado

        db.commit()
        db.refresh(cliente)
        if venta_obj:
            db.refresh(venta_obj)

    except IntegrityError as e:
        db.rollback()
        msg = str(getattr(e.orig, "args", e.args))
        raise HTTPException(status_code=400, detail=f"Violación de integridad al actualizar: {msg}")
    except SQLAlchemyError as e:
        db.rollback()
        raise HTTPException(status_code=500, detail=f"SQLAlchemyError: {e}")
    except Exception as e:
        db.rollback()
        raise HTTPException(status_code=500, detail=f"Error al actualizar cliente y venta: {e}")

    return CrearClienteYVentaResponse(
        cliente=ClienteOut.model_validate(cliente),
        venta=VentaMembresiaOut.model_validate(venta_obj) if venta_obj else None,
    )

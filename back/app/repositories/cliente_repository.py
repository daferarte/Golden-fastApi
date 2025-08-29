from sqlalchemy.orm import Session
from datetime import date
from app.models.cliente import Cliente
from app.schemas.cliente import ClienteCreate, ClienteBase
from .base import BaseRepository
from typing import Optional, List, Tuple
from sqlalchemy import asc, select, func, and_, desc, case
from sqlalchemy import func, or_
from app.models.venta_membresia import VentaMembresia

class ClienteRepository(BaseRepository):
    def __init__(self):
        super().__init__(Cliente)

    def get_by_documento(self, db: Session, documento: str):
        return db.query(Cliente).filter(Cliente.documento == documento).first()
    
    def get_by_huella(self, db: Session, huella_template: bytes):
        return db.query(Cliente).filter(Cliente.huella_template == huella_template).first()
    
    def get_all_with_huella(self, db: Session):
        """
        Obtiene todos los clientes que tienen una plantilla de huella no nula.
        """
        return db.query(Cliente).filter(Cliente.huella_template != None).all()
    
    def update_huella(self, db: Session, cliente_id: int, nueva_huella: bytes):
        """
        Busca un cliente por su ID y actualiza su campo de huella.
        """
        cliente = db.query(Cliente).filter(Cliente.id == cliente_id).first()
        if cliente:
            cliente.huella_template = nueva_huella
            db.commit()
            db.refresh(cliente)
        return cliente
    
    def find_next_available_huella_id(self, db: Session) -> int:
        """
        Encuentra el primer ID de huella consecutivo que está libre.
        Ej: Si existen [1, 2, 4], esta función devolverá 3.
        Si existen [1, 2, 3], devolverá 4.
        Si no existe ninguno, devolverá 1.
        """
        # Obtenemos todos los id_huella que no son nulos y los ordenamos
        used_ids = db.query(self.model.id_huella)\
                     .filter(self.model.id_huella != None)\
                     .order_by(self.model.id_huella)\
                     .all()
        
        # 'used_ids' será una lista de tuplas, ej: [(1,), (2,), (4,)]
        # La convertimos a una lista de enteros
        used_ids = [item[0] for item in used_ids]

        expected_id = 1
        for used_id in used_ids:
            if used_id != expected_id:
                # Encontramos un hueco, ej: el ID 3 no está usado
                return expected_id
            expected_id += 1
        
        # Si no se encontraron huecos, usamos el siguiente número después del más alto
        return expected_id
    
    def get_by_id_huella(self, db: Session, id_huella: int):
        """
        Busca un cliente específico usando su id_huella.
        """
        return db.query(Cliente).filter(Cliente.id_huella == id_huella).first()
    
    def find_next_available_huella_id(self, db: Session) -> int:
        """
        Encuentra el primer ID de huella consecutivo que está libre.
        Ej: Si existen [1, 2, 4] -> 3. Si existen [1, 2, 3] -> 4. Si no hay, -> 1.
        """
        used_ids = (
            db.query(self.model.id_huella)
              .filter(self.model.id_huella != None)
              .order_by(self.model.id_huella)
              .all()
        )
        used_ids = [row[0] for row in used_ids]
        expected_id = 1
        for used_id in used_ids:
            if used_id != expected_id:
                return expected_id
            expected_id += 1
        return expected_id
    
    # ---------------------------
    # 🔎 Filtro de búsqueda común
    # ---------------------------
    def _apply_filter(self, query, q: Optional[str]):
        if q:
            pattern = f"%{q}%"
            # Con MySQL y collation utf8mb4_unicode_ci, LIKE es case-insensitive.
            query = query.filter(
                or_(
                    self.model.nombre.like(pattern),
                    self.model.apellido.like(pattern),
                    self.model.documento.like(pattern),
                    self.model.correo.like(pattern),
                )
            )
        return query

    # ---------------------------
    # 📊 Conteo total con filtro
    # ---------------------------
    def count_filtered(self, db: Session, q: Optional[str]) -> int:
        query = db.query(func.count(self.model.id))
        query = self._apply_filter(query.select_from(self.model), q)
        return query.scalar() or 0

    # ---------------------------
    # 📃 Página de resultados
    # ---------------------------
    def find_filtered_paginated(
        self,
        db: Session,
        q: Optional[str],
        sort_attr: str,
        descending: bool,
        offset: int,
        limit: int,
    ) -> List[Cliente]:
        query = db.query(self.model)
        query = self._apply_filter(query, q)

        # Orden seguro por atributo permitido (validado en el service/endpoint)
        column = getattr(self.model, sort_attr)
        query = query.order_by(column.desc() if descending else column.asc())

        return query.offset(offset).limit(limit).all()
    
    def _compute_estado(self, fecha_fin: Optional[date], sesiones_restantes: Optional[int], estado_db: Optional[str]) -> str:
        """
        Si DB ya tiene 'estado', úsalo como preferencia.
        Si no, calculamos:
        - vencida si fecha_fin < hoy o sesiones_restantes <= 0
        - activa si hay venta vigente
        - sin_membresia si no hay venta
        """
        if estado_db:
            return estado_db

        if fecha_fin is None and sesiones_restantes is None:
            return "sin_membresia"

        today = date.today()
        if (fecha_fin is not None and fecha_fin < today) or (sesiones_restantes is not None and sesiones_restantes <= 0):
            return "vencida"
        return "activa"
    
    def get_membership_summary_by_cliente_id(self, db: Session, cliente_id: int) -> Optional[dict]:
        """
        Última venta de membresía para un cliente (por fecha_inicio DESC)
        """
        # subquery: última venta por fecha_inicio
        subq = (
            select(VentaMembresia.id, VentaMembresia.id_cliente)
            .where(VentaMembresia.id_cliente == cliente_id)
            .order_by(VentaMembresia.fecha_inicio.desc())
            .limit(1)
            .subquery()
        )

        stmt = (
            select(
                Cliente.id.label("id"),
                Cliente.fotografia.label("foto"),
                Cliente.nombre,
                Cliente.apellido,
                Cliente.documento,
                VentaMembresia.fecha_inicio,
                VentaMembresia.fecha_fin,
                VentaMembresia.precio_final.label("precio"),
                VentaMembresia.sesiones_restantes,
                VentaMembresia.estado,
            )
            .select_from(Cliente)
            .join(subq, subq.c.id_cliente == Cliente.id, isouter=True)
            .join(VentaMembresia, VentaMembresia.id == subq.c.id, isouter=True)
            .where(Cliente.id == cliente_id)
        )

        row = db.execute(stmt).mappings().first()
        if not row:
            return None

        estado = self._compute_estado(row.get("fecha_fin"), row.get("sesiones_restantes"), row.get("estado"))
        return {
            "id": row["id"],
            "foto": row.get("foto"),
            "nombre": row["nombre"],
            "apellido": row["apellido"],
            "documento": row["documento"],
            "fecha_inicio": row.get("fecha_inicio"),
            "fecha_fin": row.get("fecha_fin"),
            "precio": float(row["precio"]) if row.get("precio") is not None else None,
            "sesiones_restantes": row.get("sesiones_restantes"),
            "estado": estado,
        }
        
    def count_membership_summaries(self, db: Session, q: Optional[str]) -> int:
        """
        Total de clientes que matchean el filtro (sobre datos del cliente).
        """
        stmt = select(func.count(Cliente.id))
        if q:
            like = f"%{q}%"
            stmt = stmt.where(
                func.concat(Cliente.nombre, " ", Cliente.apellido).like(like) |
                Cliente.documento.like(like) |
                Cliente.correo.like(like)
            )
        return db.scalar(stmt) or 0

    def list_membership_summaries_paginated(
        self,
        db: Session,
        q: Optional[str],
        offset: int,
        limit: int,
        order_by_fecha_inicio_desc: bool = True,
    ) -> List[dict]:
        """
        Lista paginada: para cada cliente, su última venta de membresía (si existe).
        """
        # subquery: última fecha por cliente
        latest_per_cliente = (
            select(
                VentaMembresia.id_cliente.label("id_cliente"),
                func.max(VentaMembresia.fecha_inicio).label("max_fecha")
            )
            .group_by(VentaMembresia.id_cliente)
            .subquery()
        )

        stmt = (
            select(
                Cliente.id.label("id"),
                Cliente.fotografia.label("foto"),
                Cliente.nombre,
                Cliente.apellido,
                Cliente.documento,
                VentaMembresia.fecha_inicio,
                VentaMembresia.fecha_fin,
                VentaMembresia.precio_final.label("precio"),
                VentaMembresia.sesiones_restantes,
                VentaMembresia.estado,
            )
            .select_from(Cliente)
            .join(latest_per_cliente, latest_per_cliente.c.id_cliente == Cliente.id, isouter=True)
            .join(
                VentaMembresia,
                and_(
                    VentaMembresia.id_cliente == latest_per_cliente.c.id_cliente,
                    VentaMembresia.fecha_inicio == latest_per_cliente.c.max_fecha,
                ),
                isouter=True,
            )
        )

        if q:
            like = f"%{q}%"
            stmt = stmt.where(
                func.concat(Cliente.nombre, " ", Cliente.apellido).like(like) |
                Cliente.documento.like(like) |
                Cliente.correo.like(like)
            )

        # Orden: por última fecha_inicio (desc) o por nombre
        if order_by_fecha_inicio_desc:
            stmt = stmt.order_by(VentaMembresia.fecha_inicio.is_(None).asc(),
                     VentaMembresia.fecha_inicio.desc())
        else:
            stmt = stmt.order_by(Cliente.nombre.asc(), Cliente.apellido.asc())

        stmt = stmt.offset(offset).limit(limit)

        rows = db.execute(stmt).mappings().all()
        out: List[dict] = []
        for r in rows:
            estado = self._compute_estado(r.get("fecha_fin"), r.get("sesiones_restantes"), r.get("estado"))
            out.append({
                "id": r["id"],
                "foto": r.get("foto"),
                "nombre": r["nombre"],
                "apellido": r["apellido"],
                "documento": r["documento"],
                "fecha_inicio": r.get("fecha_inicio"),
                "fecha_fin": r.get("fecha_fin"),
                "precio": float(r["precio"]) if r.get("precio") is not None else None,
                "sesiones_restantes": r.get("sesiones_restantes"),
                "estado": estado,
            })
        return out
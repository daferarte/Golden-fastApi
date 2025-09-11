from datetime import datetime, timedelta
from typing import List, Optional

from sqlalchemy.orm import Session, joinedload, load_only
from sqlalchemy import func, and_

from app.models.asistencia import Asistencia
from app.models.cliente import Cliente
from app.models.venta_membresia import VentaMembresia
from .base import BaseRepository
class AsistenciaRepository(BaseRepository):
    def __init__(self):
        super().__init__(Asistencia)

    def count_today_for_client(self, db: Session, cliente_id: int):
        now = datetime.now()
        start = now.replace(hour=0, minute=0, second=0, microsecond=0)
        end = start + timedelta(days=1)
        return db.query(func.count(Asistencia.id)).filter(
            Asistencia.id_cliente == cliente_id,
            Asistencia.fecha_hora_entrada >= start,
            Asistencia.fecha_hora_entrada < end
        ).scalar() or 0
        
    def get_all_with_relations(
        self,
        db: Session,
        *,
        limit: Optional[int] = None,
        offset: int = 0,
        cliente_id: Optional[int] = None,
        sede_id: Optional[int] = None,
        fecha_desde: Optional[datetime] = None,
        fecha_hasta: Optional[datetime] = None,
        desc: bool = True,
    ) -> List[Asistencia]:
        """
        Lista de asistencias con Cliente y VentaMembresia precargadas.
        Permite filtros opcionales y paginación.
        """
        q = (
            db.query(Asistencia)
            .options(
                joinedload(Asistencia.cliente).load_only(
                    Cliente.id, Cliente.documento, Cliente.nombre, Cliente.apellido, Cliente.fotografia
                ),
                joinedload(Asistencia.venta).load_only(
                    VentaMembresia.id,
                    VentaMembresia.fecha_inicio,
                    VentaMembresia.fecha_fin,
                    VentaMembresia.estado,
                    VentaMembresia.sesiones_restantes,
                ),
            )
        )

        # Filtros opcionales
        if cliente_id is not None:
            q = q.filter(Asistencia.id_cliente == cliente_id)
        if sede_id is not None:
            q = q.filter(Asistencia.id_sede == sede_id)
        if fecha_desde is not None:
            q = q.filter(Asistencia.fecha_hora_entrada >= fecha_desde)
        if fecha_hasta is not None:
            q = q.filter(Asistencia.fecha_hora_entrada < fecha_hasta)

        # Orden
        q = q.order_by(
            Asistencia.fecha_hora_entrada.desc() if desc else Asistencia.fecha_hora_entrada.asc()
        )

        # Paginación
        if offset:
            q = q.offset(offset)
        if limit is not None:
            q = q.limit(limit)

        return q.all()

    def get_by_id_with_relations(self, db: Session, asistencia_id: int) -> Optional[Asistencia]:
        """
        Una asistencia por id con Cliente y VentaMembresia precargadas.
        """
        return (
            db.query(Asistencia)
            .options(
                joinedload(Asistencia.cliente).load_only(
                    Cliente.id, Cliente.documento, Cliente.nombre, Cliente.apellido, Cliente.fotografia
                ),
                joinedload(Asistencia.venta).load_only(
                    VentaMembresia.id,
                    VentaMembresia.fecha_inicio,
                    VentaMembresia.fecha_fin,
                    VentaMembresia.estado,
                    VentaMembresia.sesiones_restantes,
                ),
            )
            .filter(Asistencia.id == asistencia_id)
            .first()
        )

    # (Opcional) Conteo con los mismos filtros de get_all_with_relations
    def count_with_filters(
        self,
        db: Session,
        *,
        cliente_id: Optional[int] = None,
        sede_id: Optional[int] = None,
        fecha_desde: Optional[datetime] = None,
        fecha_hasta: Optional[datetime] = None,
    ) -> int:
        q = db.query(func.count(Asistencia.id))
        if cliente_id is not None:
            q = q.filter(Asistencia.id_cliente == cliente_id)
        if sede_id is not None:
            q = q.filter(Asistencia.id_sede == sede_id)
        if fecha_desde is not None:
            q = q.filter(Asistencia.fecha_hora_entrada >= fecha_desde)
        if fecha_hasta is not None:
            q = q.filter(Asistencia.fecha_hora_entrada < fecha_hasta)
        return q.scalar() or 0
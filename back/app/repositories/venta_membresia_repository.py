from sqlalchemy.orm import Session
from datetime import date
from app.models.venta_membresia import VentaMembresia
from .base import BaseRepository

class VentaMembresiaRepository(BaseRepository):
    def __init__(self):
        super().__init__(VentaMembresia)

    def find_active_for_client(self, db: Session, cliente_id: int):
        """
        Encuentra la última membresía activa (no vencida) para un cliente.
        """
        return db.query(VentaMembresia).filter(
            VentaMembresia.id_cliente == cliente_id,
            VentaMembresia.fecha_fin >= date.today()
        ).order_by(VentaMembresia.fecha_fin.desc()).first()
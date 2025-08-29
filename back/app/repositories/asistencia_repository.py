from sqlalchemy.orm import Session
from sqlalchemy import func
from datetime import date
from app.models.asistencia import Asistencia
from .base import BaseRepository


class AsistenciaRepository(BaseRepository):
    def __init__(self):
        super().__init__(Asistencia)

    def count_today_for_client(self, db: Session, cliente_id: int):
        """
        Cuenta los registros de asistencia de un cliente para el día de hoy.
        """
        today = date.today()
        
        sesiones= db.query(func.count(Asistencia.id)).filter(
            Asistencia.id_cliente == cliente_id,
            func.date(Asistencia.fecha_hora_entrada) == today
        ).scalar() or 0
        
        return sesiones
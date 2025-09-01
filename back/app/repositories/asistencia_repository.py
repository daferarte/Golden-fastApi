from sqlalchemy.orm import Session
from sqlalchemy import func
from datetime import date
from app.models.asistencia import Asistencia
from .base import BaseRepository
from datetime import datetime, timedelta

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
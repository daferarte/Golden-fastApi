from app.models.reporte_asistencia import ReporteAsistencia
from .base import BaseRepository

class ReporteAsistenciaRepository(BaseRepository):
    def __init__(self):
        super().__init__(ReporteAsistencia)

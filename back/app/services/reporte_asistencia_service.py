from app.repositories.reporte_asistencia_repository import ReporteAsistenciaRepository
from .base_service import BaseService

class ReporteAsistenciaService(BaseService):
    def __init__(self):
        super().__init__(ReporteAsistenciaRepository())

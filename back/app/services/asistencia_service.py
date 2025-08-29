from app.repositories.asistencia_repository import AsistenciaRepository
from .base_service import BaseService

class AsistenciaService(BaseService):
    def __init__(self):
        super().__init__(AsistenciaRepository())

# app/services/asistencia_service.py
from sqlalchemy.orm import Session
from app.repositories.asistencia_repository import AsistenciaRepository
from .base_service import BaseService

class AsistenciaService(BaseService):
    def __init__(self):
        super().__init__(AsistenciaRepository())

    def get_all(self, db: Session):
        return self.repository.get_all_with_relations(db)

    def get_by_id(self, db: Session, asistencia_id: int):
        return self.repository.get_by_id_with_relations(db, asistencia_id)

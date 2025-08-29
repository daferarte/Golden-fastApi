from app.repositories.membresia_repository import MembresiaRepository
from .base_service import BaseService

class MembresiaService(BaseService):
    def __init__(self):
        super().__init__(MembresiaRepository())

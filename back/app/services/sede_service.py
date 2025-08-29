from app.repositories.sede_repository import SedeRepository
from .base_service import BaseService

class SedeService(BaseService):
    def __init__(self):
        super().__init__(SedeRepository())

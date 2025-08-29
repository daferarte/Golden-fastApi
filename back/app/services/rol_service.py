from app.repositories.rol_repository import RolRepository
from .base_service import BaseService

class RolService(BaseService):
    def __init__(self):
        super().__init__(RolRepository())

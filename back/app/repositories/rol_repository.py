from app.models.rol import Rol
from .base import BaseRepository

class RolRepository(BaseRepository):
    def __init__(self):
        super().__init__(Rol)

from app.models.membresia import Membresia
from .base import BaseRepository

class MembresiaRepository(BaseRepository):
    def __init__(self):
        super().__init__(Membresia)

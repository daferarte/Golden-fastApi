from app.models.sede import Sede
from .base import BaseRepository

class SedeRepository(BaseRepository):
    def __init__(self):
        super().__init__(Sede)

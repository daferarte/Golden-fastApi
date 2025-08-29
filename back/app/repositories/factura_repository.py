from app.models.factura import Factura
from .base import BaseRepository

class FacturaRepository(BaseRepository):
    def __init__(self):
        super().__init__(Factura)

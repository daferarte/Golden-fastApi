from app.models.tipo_descuento import TipoDescuento
from .base import BaseRepository

class TipoDescuentoRepository(BaseRepository):
    def __init__(self):
        super().__init__(TipoDescuento)

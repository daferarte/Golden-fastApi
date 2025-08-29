from app.models.detalle_factura import DetalleFactura
from .base import BaseRepository

class DetalleFacturaRepository(BaseRepository):
    def __init__(self):
        super().__init__(DetalleFactura)

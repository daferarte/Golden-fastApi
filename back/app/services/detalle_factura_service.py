from app.repositories.detalle_factura_repository import DetalleFacturaRepository
from .base_service import BaseService

class DetalleFacturaService(BaseService):
    def __init__(self):
        super().__init__(DetalleFacturaRepository())

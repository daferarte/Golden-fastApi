from app.repositories.factura_repository import FacturaRepository
from .base_service import BaseService

class FacturaService(BaseService):
    def __init__(self):
        super().__init__(FacturaRepository())

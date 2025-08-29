from app.repositories.venta_membresia_repository import VentaMembresiaRepository
from .base_service import BaseService

class VentaMembresiaService(BaseService):
    def __init__(self):
        super().__init__(VentaMembresiaRepository())

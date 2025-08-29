from app.repositories.tipo_descuento_repository import TipoDescuentoRepository
from .base_service import BaseService

class TipoDescuentoService(BaseService):
    def __init__(self):
        super().__init__(TipoDescuentoRepository())

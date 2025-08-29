from fastapi import HTTPException
from sqlalchemy.orm import Session
from app.repositories.cliente_repository import ClienteRepository
from .base_service import BaseService
from .fingerprint import Fingerprint  # <-- IMPORTANTE: Importa la clase del archivo local
from typing import Optional, Tuple, List
from app.schemas.membresia_resumen import ResumenMembresia

class ClienteService(BaseService):
    def __init__(self):
        super().__init__(ClienteRepository())
        print("✓ Servicio de comparación de huellas local inicializado.")

    def create(self, db: Session, obj_in):
        # 1. Verificar si el cliente ya existe por documento
        existente = self.repository.get_by_documento(db, obj_in.documento)
        if existente:
            raise HTTPException(status_code=400, detail="Cliente ya existe con este documento")

        # 2. Si se está agregando una huella, asignarle el siguiente ID disponible
        if obj_in.huella_template:
            next_huella_id = self.repository.find_next_available_huella_id(db)
            obj_in.id_huella = next_huella_id
        
        # 3. Crear el cliente
        return super().create(db, obj_in)
    
    def update(self, db: Session, id_value: int, obj_in):
        db_obj = self.repository.get_by_id(db, id_value)
        if not db_obj:
            raise HTTPException(status_code=404, detail="Recurso no encontrado")

        # --- Lógica de gestión de id_huella en la actualización ---
        
        # CASO 1: Se está agregando una huella a un cliente que NO tenía
        if obj_in.huella_template and not db_obj.huella_template:
            obj_in.id_huella = self.repository.find_next_available_huella_id(db)

        # CASO 2: Se está eliminando la huella de un cliente que SÍ tenía
        elif not obj_in.huella_template and db_obj.huella_template:
            # Liberamos el id_huella para que pueda ser reutilizado
            obj_in.id_huella = None
        
        # CASO 3: Se está actualizando una huella existente. Mantenemos el mismo id_huella.
        elif obj_in.huella_template and db_obj.huella_template:
            obj_in.id_huella = db_obj.id_huella

        return self.repository.update(db, db_obj, obj_in)

    def delete(self, db: Session, id_value: int):
        # No se necesita lógica adicional aquí.
        # Al eliminar el cliente, la fila desaparece y el id_huella queda
        # automáticamente libre para que find_next_available_huella_id lo encuentre.
        return super().delete(db, id_value)
    
    def update_huella(self, db: Session, cliente_id: int, nueva_huella: bytes):
        """
        Actualiza la plantilla de la huella para un cliente existente.
        Llama al repositorio para realizar el cambio en la base de datos.
        """
        cliente_actualizado = self.repository.update_huella(db, cliente_id, nueva_huella)
        if not cliente_actualizado:
            raise HTTPException(status_code=404, detail="Cliente no encontrado al intentar actualizar la huella.")
        return cliente_actualizado
    
    def get_all_with_huella(self, db: Session):
        """
        Llama al método del repositorio que obtiene solo clientes con huella.
        """
        return self.repository.get_all_with_huella(db)
    
    def get_paginated(
        self,
        db: Session,
        page: int,
        size: int,
        q: Optional[str],
        sort_attr: str,
        descending: bool,
    ) -> Tuple[int, list, int, int]:
        """
        Retorna (total, items, pages, page_ajustada)
        """
        total = self.repository.count_filtered(db, q=q)
        pages = (total + size - 1) // size if total else 1
        if page > pages and total > 0:
            page = pages

        offset = (page - 1) * size
        items = self.repository.find_filtered_paginated(
            db,
            q=q,
            sort_attr=sort_attr,
            descending=descending,
            offset=offset,
            limit=size,
        )
        return total, items, pages, page
    
    def get_membership_summary(self, db: Session, cliente_id: int) -> Optional[ResumenMembresia]:
        data = self.repository.get_membership_summary_by_cliente_id(db, cliente_id)
        return ResumenMembresia(**data) if data else None

    def list_membership_summaries(
        self,
        db: Session,
        page: int,
        size: int,
        q: Optional[str],
    ) -> Tuple[int, List[ResumenMembresia]]:
        total = self.repository.count_membership_summaries(db, q=q)
        offset = (max(page, 1) - 1) * size
        rows = self.repository.list_membership_summaries_paginated(db, q=q, offset=offset, limit=size)
        return total, [ResumenMembresia(**r) for r in rows]
from sqlalchemy.orm import Session

from app.models.cliente import Cliente
from app.schemas.cliente import ClienteCreate, ClienteBase
from .base import BaseRepository
from typing import Optional, List
from sqlalchemy import asc, desc
from sqlalchemy import func, or_

class ClienteRepository(BaseRepository):
    def __init__(self):
        super().__init__(Cliente)

    def get_by_documento(self, db: Session, documento: str):
        return db.query(Cliente).filter(Cliente.documento == documento).first()
    
    def get_by_huella(self, db: Session, huella_template: bytes):
        return db.query(Cliente).filter(Cliente.huella_template == huella_template).first()
    
    def get_all_with_huella(self, db: Session):
        """
        Obtiene todos los clientes que tienen una plantilla de huella no nula.
        """
        return db.query(Cliente).filter(Cliente.huella_template != None).all()
    
    def update_huella(self, db: Session, cliente_id: int, nueva_huella: bytes):
        """
        Busca un cliente por su ID y actualiza su campo de huella.
        """
        cliente = db.query(Cliente).filter(Cliente.id == cliente_id).first()
        if cliente:
            cliente.huella_template = nueva_huella
            db.commit()
            db.refresh(cliente)
        return cliente
    
    def find_next_available_huella_id(self, db: Session) -> int:
        """
        Encuentra el primer ID de huella consecutivo que está libre.
        Ej: Si existen [1, 2, 4], esta función devolverá 3.
        Si existen [1, 2, 3], devolverá 4.
        Si no existe ninguno, devolverá 1.
        """
        # Obtenemos todos los id_huella que no son nulos y los ordenamos
        used_ids = db.query(self.model.id_huella)\
                     .filter(self.model.id_huella != None)\
                     .order_by(self.model.id_huella)\
                     .all()
        
        # 'used_ids' será una lista de tuplas, ej: [(1,), (2,), (4,)]
        # La convertimos a una lista de enteros
        used_ids = [item[0] for item in used_ids]

        expected_id = 1
        for used_id in used_ids:
            if used_id != expected_id:
                # Encontramos un hueco, ej: el ID 3 no está usado
                return expected_id
            expected_id += 1
        
        # Si no se encontraron huecos, usamos el siguiente número después del más alto
        return expected_id
    
    def get_by_id_huella(self, db: Session, id_huella: int):
        """
        Busca un cliente específico usando su id_huella.
        """
        return db.query(Cliente).filter(Cliente.id_huella == id_huella).first()
    
    def find_next_available_huella_id(self, db: Session) -> int:
        """
        Encuentra el primer ID de huella consecutivo que está libre.
        Ej: Si existen [1, 2, 4] -> 3. Si existen [1, 2, 3] -> 4. Si no hay, -> 1.
        """
        used_ids = (
            db.query(self.model.id_huella)
              .filter(self.model.id_huella != None)
              .order_by(self.model.id_huella)
              .all()
        )
        used_ids = [row[0] for row in used_ids]
        expected_id = 1
        for used_id in used_ids:
            if used_id != expected_id:
                return expected_id
            expected_id += 1
        return expected_id
    
    # ---------------------------
    # 🔎 Filtro de búsqueda común
    # ---------------------------
    def _apply_filter(self, query, q: Optional[str]):
        if q:
            pattern = f"%{q}%"
            # Con MySQL y collation utf8mb4_unicode_ci, LIKE es case-insensitive.
            query = query.filter(
                or_(
                    self.model.nombre.like(pattern),
                    self.model.apellido.like(pattern),
                    self.model.documento.like(pattern),
                    self.model.correo.like(pattern),
                )
            )
        return query

    # ---------------------------
    # 📊 Conteo total con filtro
    # ---------------------------
    def count_filtered(self, db: Session, q: Optional[str]) -> int:
        query = db.query(func.count(self.model.id))
        query = self._apply_filter(query.select_from(self.model), q)
        return query.scalar() or 0

    # ---------------------------
    # 📃 Página de resultados
    # ---------------------------
    def find_filtered_paginated(
        self,
        db: Session,
        q: Optional[str],
        sort_attr: str,
        descending: bool,
        offset: int,
        limit: int,
    ) -> List[Cliente]:
        query = db.query(self.model)
        query = self._apply_filter(query, q)

        # Orden seguro por atributo permitido (validado en el service/endpoint)
        column = getattr(self.model, sort_attr)
        query = query.order_by(column.desc() if descending else column.asc())

        return query.offset(offset).limit(limit).all()
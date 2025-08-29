from fastapi import HTTPException
from sqlalchemy.orm import Session

class BaseService:
    def __init__(self, repository):
        self.repository = repository

    def get_all(self, db: Session):
        return self.repository.get_all(db)

    def get_by_id(self, db: Session, id_value: int):
        obj = self.repository.get_by_id(db, id_value)
        if not obj:
            raise HTTPException(status_code=404, detail="Recurso no encontrado")
        return obj

    def create(self, db: Session, obj_in):
        return self.repository.create(db, obj_in)

    def update(self, db: Session, id_value: int, obj_in):
        db_obj = self.repository.get_by_id(db, id_value)
        if not db_obj:
            raise HTTPException(status_code=404, detail="Recurso no encontrado")
        return self.repository.update(db, db_obj, obj_in)

    def delete(self, db: Session, id_value: int):
        obj = self.repository.delete(db, id_value)
        if not obj:
            raise HTTPException(status_code=404, detail="Recurso no encontrado")
        return obj

from sqlalchemy.orm import Session

class BaseRepository:
    def __init__(self, model):
        self.model = model

    def get_all(self, db: Session):
        return db.query(self.model).all()

    def get_by_id(self, db: Session, id_value: int):
        return db.query(self.model).filter(self.model.id == id_value).first()

    def create(self, db: Session, obj_in):
        db_obj = self.model(**obj_in.dict())
        db.add(db_obj)
        db.commit()
        db.refresh(db_obj)
        return db_obj

    def update(self, db: Session, db_obj, obj_in):
        for field, value in obj_in.dict(exclude_unset=True).items():
            setattr(db_obj, field, value)
        db.commit()
        db.refresh(db_obj)
        return db_obj

    def delete(self, db: Session, id_value: int):
        obj = self.get_by_id(db, id_value)
        if obj:
            db.delete(obj)
            db.commit()
        return obj

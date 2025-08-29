from sqlalchemy import Column, Integer, String
from sqlalchemy.orm import relationship
from app.db.base_class import Base

class Rol(Base):
    __tablename__ = 'rol'

    id = Column(Integer, primary_key=True, index=True)
    nombre_rol = Column(String(120))
    descripcion = Column(String(255))

    usuarios = relationship('Usuario', back_populates='rol')
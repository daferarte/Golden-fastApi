from sqlalchemy import Column, Integer, String, Float
from sqlalchemy.orm import relationship
from app.db.base_class import Base

class TipoDescuento(Base):
    __tablename__ = 'tipo_descuento'

    id = Column(Integer, primary_key=True, index=True)
    nombre_descuento = Column(String(120), nullable=False)
    porcentaje_descuento = Column(Float, nullable=False, default=0.0)

    clientes = relationship('Cliente', backref='tipo_descuento')
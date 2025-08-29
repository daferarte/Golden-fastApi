from sqlalchemy import Column, Integer, ForeignKey, DateTime, Float, String
from sqlalchemy.orm import relationship
from app.db.base_class import Base

class VentaMembresia(Base):
    __tablename__ = 'venta_membresia'

    id = Column(Integer, primary_key=True, index=True)
    id_cliente = Column(Integer, ForeignKey('cliente.id'))
    id_membresia = Column(Integer, ForeignKey('membresia.id'))
    fecha_inicio = Column(DateTime)
    fecha_fin = Column(DateTime)
    precio_final = Column(Float)
    estado = Column(String(120))
    sesiones_restantes = Column(Integer)

    cliente = relationship('Cliente', back_populates='ventas')
    
    membresia = relationship('Membresia', back_populates='ventas')
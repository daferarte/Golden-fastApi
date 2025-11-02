from sqlalchemy import Column, Integer, ForeignKey, DateTime, String, Text
from sqlalchemy.orm import relationship
from app.db.base_class import Base

class Asistencia(Base):
    __tablename__ = 'asistencia'

    id = Column(Integer, primary_key=True, index=True)
    id_cliente = Column(Integer, ForeignKey('cliente.id'))
    id_venta = Column(Integer, ForeignKey('venta_membresia.id'))
    id_sede = Column(Integer, ForeignKey('sede.id'))
    fecha_hora_entrada = Column(DateTime)
    tipo_acceso = Column(String(120))
    motivo_error = Column(Text, nullable=True)
    
    cliente = relationship('Cliente', back_populates='asistencias')
    venta = relationship('VentaMembresia', back_populates='asistencias')
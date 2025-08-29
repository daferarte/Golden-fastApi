from sqlalchemy import Column, Integer, String, Float
from sqlalchemy.orm import relationship  # Asegúrate de importar relationship
from app.db.base_class import Base

class Membresia(Base):
    __tablename__ = 'membresia'

    id = Column(Integer, primary_key=True, index=True)
    nombre_membresia = Column(String(120), nullable=False)
    duracion_dias = Column(Integer, nullable=False)
    cantidad_sesiones = Column(Integer, nullable=True)
    precio_base = Column(Float, nullable=False)
    max_accesos_diarios = Column(Integer, nullable=True)
    
    ventas = relationship('VentaMembresia', back_populates='membresia')
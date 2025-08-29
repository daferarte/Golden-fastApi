from sqlalchemy import Column, Integer, String, Date, ForeignKey, LargeBinary
from sqlalchemy.orm import relationship
from app.db.base_class import Base

class Cliente(Base):
    __tablename__ = 'cliente'

    id = Column(Integer, primary_key=True, index=True)
    nombre = Column(String(120), nullable=False)
    apellido = Column(String(120), nullable=False)
    documento = Column(String(20), unique=True, nullable=False)
    id_huella = Column(Integer, unique=True, nullable=True, index=True)
    fecha_nacimiento = Column(Date, nullable=False)
    telefono = Column(String(120), nullable=True)
    correo = Column(String(120), nullable=False, unique=True)
    direccion = Column(String(120), nullable=True)
    id_tipo_descuento = Column(Integer, ForeignKey('tipo_descuento.id'), nullable=True)
    huella_template = Column(LargeBinary, nullable=True)
    fotografia = Column(String(255), nullable=True)

    ventas = relationship('VentaMembresia', back_populates='cliente')
    asistencias = relationship('Asistencia', back_populates='cliente')
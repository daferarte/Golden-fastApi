from sqlalchemy import Column, Integer, String, Boolean, ForeignKey
from sqlalchemy.orm import relationship
from app.db.base_class import Base

class Usuario(Base):
    __tablename__ = 'usuario'

    id = Column(Integer, primary_key=True, index=True)
    nombre_usuario = Column(String(120), unique=True, index=True, nullable=False)
    contraseña_hash = Column(String(120), nullable=False)
    correo = Column(String(120), unique=True, nullable=False)
    activo = Column(Boolean, default=True)
    id_rol = Column(Integer, ForeignKey('rol.id'))
    id_cliente = Column(Integer, ForeignKey('cliente.id'), nullable=True)

    rol = relationship('Rol', back_populates='usuarios')
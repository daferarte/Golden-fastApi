from sqlalchemy import Column, Integer, String
from sqlalchemy.orm import relationship
from app.db.base_class import Base

class Sede(Base):
    __tablename__ = 'sede'

    id = Column(Integer, primary_key=True, index=True, autoincrement=True)
    nombre_sede = Column(String(120), nullable=False)
    direccion = Column(String(120))
    telefono = Column(String(12))

    asistencias = relationship('Asistencia', backref='sede')
    reportes = relationship('ReporteAsistencia', backref='sede')
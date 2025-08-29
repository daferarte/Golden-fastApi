from sqlalchemy import Column, Integer, ForeignKey, DateTime, String, Text, Boolean
from sqlalchemy.orm import relationship
from app.db.base_class import Base

class ReporteAsistencia(Base):
    __tablename__ = 'reporte_asistencia'

    id = Column(Integer, primary_key=True, index=True)
    id_cliente = Column(Integer, ForeignKey('cliente.id'), nullable=True)
    id_sede = Column(Integer, ForeignKey('sede.id'), nullable=True)
    fecha_generacion = Column(DateTime)
    tipo_reporte = Column(String(120))
    contenido = Column(Text)
    enviado = Column(Boolean, default=False)
    fecha_envio = Column(DateTime, nullable=True)
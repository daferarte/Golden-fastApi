from sqlalchemy import Column, Integer, String, DateTime, Float, ForeignKey
from sqlalchemy.orm import relationship
from app.db.base_class import Base

class Factura(Base):
    __tablename__ = 'factura'

    id = Column(Integer, primary_key=True, index=True)
    numero_factura = Column(String(120), nullable=False)
    fecha_emision = Column(DateTime)
    id_cliente = Column(Integer, ForeignKey('cliente.id'))
    subtotal = Column(Float)
    descuento_total = Column(Float)
    total = Column(Float)
    metodo_pago = Column(String(120))
    estado = Column(String(120))

    detalles = relationship('DetalleFactura', back_populates='factura')
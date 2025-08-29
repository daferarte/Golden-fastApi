from sqlalchemy import Column, Integer, Float, ForeignKey, String
from sqlalchemy.orm import relationship
from app.db.base_class import Base

class DetalleFactura(Base):
    __tablename__ = 'detalle_factura'

    id = Column(Integer, primary_key=True, index=True)
    id_factura = Column(Integer, ForeignKey('factura.id'))
    id_venta = Column(Integer, ForeignKey('venta_membresia.id'))
    descripcion = Column(String(120))
    cantidad = Column(Integer)
    precio_unitario = Column(Float)
    descuento_aplicado = Column(Float)
    total_linea = Column(Float)

    factura = relationship('Factura', back_populates='detalles')
# from sqlalchemy.orm import declarative_base

# Base = declarative_base()

# # Aquí se importan los modelos para que Alembic y create_all los conozcan
# from app.models import asistencia, cliente, detalle_factura, factura, membresia, reporte_asistencia, rol, sede, tipo_descuento, usuario, venta_membresia

from app.db.base_class import Base  # Clase declarativa base

# Importar todos los modelos para que Alembic los detecte
from app.models.sede import Sede
from app.models.cliente import Cliente
from app.models.tipo_descuento import TipoDescuento
from app.models.membresia import Membresia
from app.models.venta_membresia import VentaMembresia
from app.models.asistencia import Asistencia
from app.models.factura import Factura
from app.models.detalle_factura import DetalleFactura
from app.models.usuario import Usuario
from app.models.rol import Rol
from app.models.reporte_asistencia import ReporteAsistencia


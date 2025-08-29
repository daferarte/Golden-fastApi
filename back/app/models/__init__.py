from app.db import base

# Importa todos los modelos para que Alembic los vea
from .asistencia import *
from .cliente import *
from .detalle_factura import *
from .factura import *
from .membresia import *
from .reporte_asistencia import *
from .rol import *
from .sede import *
from .tipo_descuento import *
from .usuario import *
from .venta_membresia import *

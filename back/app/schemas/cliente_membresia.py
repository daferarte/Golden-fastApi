from datetime import date
from typing import Optional, Literal
from pydantic import BaseModel, Field, ConfigDict

# --- Entrada ---

class ClienteIn(BaseModel):
    nombre: str
    apellido: str
    documento: str
    fecha_nacimiento: date = None
    correo: Optional[str] = None
    telefono: Optional[str] = None
    direccion: Optional[str] = None
    id_tipo_descuento: Optional[int] = None
    fotografia: Optional[str] = None  # si la envías como base64
    huella_base64: Optional[str] = None      # si la envías como base64
    observaciones: Optional[str] = None

class VentaMembresiaIn(BaseModel):
    id_membresia: int
    fecha_inicio: Optional[date] = None      # por defecto hoy si no envías
    fecha_fin: Optional[date] = None
    precio_final: Optional[float] = None
    sesiones_restantes: Optional[int] = None
    estado: Optional[str] = Field(default="activa")
    
class ClienteUpdateIn(BaseModel):
    nombre: Optional[str] = None
    apellido: Optional[str] = None
    documento: Optional[str] = None
    fecha_nacimiento: Optional[date] = None
    correo: Optional[str] = None
    telefono: Optional[str] = None
    id_tipo_descuento: Optional[int] = None
    direccion: Optional[str] = None
    # Si tu modelo 'fotografia' es ruta (string) puedes usar esto:
    fotografia: Optional[str] = None
    observaciones: Optional[str] = None

class VentaUpdateIn(BaseModel):
    # Si no pasas id, se tomará la venta más reciente del cliente (por fecha_inicio)
    id: Optional[int] = None
    id_membresia: Optional[int] = None
    fecha_inicio: Optional[date] = None
    fecha_fin: Optional[date] = None
    precio_final: Optional[float] = None
    sesiones_restantes: Optional[int] = None
    estado: Optional[Literal['activa', 'vencida', 'sin_membresia']] = None

class CrearClienteYVentaRequest(BaseModel):
    cliente: ClienteIn
    venta: VentaMembresiaIn

# --- Salida ---

class ClienteOut(BaseModel):
    model_config = ConfigDict(from_attributes=True)
    id: int
    nombre: str
    apellido: str
    documento: str
    correo: Optional[str] = None
    telefono: Optional[str] = None
    id_tipo_descuento: Optional[int] = None
    direccion: Optional[str] = None
    id_huella: Optional[int] = None
    observaciones: Optional[str] = None

class VentaMembresiaOut(BaseModel):
    model_config = ConfigDict(from_attributes=True)
    id: int
    id_cliente: int
    id_membresia: int
    fecha_inicio: Optional[date] = None
    fecha_fin: Optional[date] = None
    precio_final: Optional[float] = None
    sesiones_restantes: Optional[int] = None
    estado: Optional[str] = None

class CrearClienteYVentaResponse(BaseModel):
    cliente: ClienteOut
    venta: VentaMembresiaOut

class ActualizarClienteYVentaRequest(BaseModel):
    cliente: ClienteUpdateIn = Field(default_factory=ClienteUpdateIn)
    venta: VentaUpdateIn = Field(default_factory=VentaUpdateIn)
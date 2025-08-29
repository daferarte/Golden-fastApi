from pydantic import BaseModel

class MembresiaBase(BaseModel):
    nombre_membresia: str
    duracion_dias: int
    cantidad_sesiones: int
    precio_base: float
    max_accesos_diarios: int

class MembresiaCreate(MembresiaBase):
    pass

class MembresiaUpdate(MembresiaBase):
    pass

class MembresiaResponse(MembresiaBase):
    id: int
    class Config:
        orm_mode = True

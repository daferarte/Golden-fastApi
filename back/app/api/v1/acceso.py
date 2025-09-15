# app/api/v1/acceso.py
from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from pydantic import BaseModel, ConfigDict, Field, field_validator, model_validator
from typing import Optional

from app.db.session import get_db
from app.services.acceso_service import AccesoService
from app.repositories.cliente_repository import ClienteRepository

router = APIRouter()
servicio_acceso = AccesoService()
cliente_repo = ClienteRepository()


# -------- Request / Response --------
class AccesoFlexibleRequest(BaseModel):
    id_huella: Optional[int] = Field(None)
    documento: Optional[str] = Field(None, max_length=20)

    # Pydantic v2 config
    model_config = ConfigDict(extra="forbid")

    # 1) Normaliza id_huella: 0 / "0" / "" -> None
    @field_validator("id_huella", mode="before")
    @classmethod
    def _normalize_id_huella(cls, v):
        if v in (None, "", "0", 0):
            return None
        return int(v)

    # 2) Normaliza documento: strip y None si vacío
    @field_validator("documento", mode="before")
    @classmethod
    def _normalize_documento(cls, v):
        if v is None:
            return None
        v = str(v).strip()
        return v or None

    # 3) Regla XOR: exactamente uno de los dos
    @model_validator(mode="after")
    def _check_exactly_one(self):
        has_huella = self.id_huella is not None
        has_doc = self.documento is not None
        if has_huella == has_doc:  # ambos True o ambos False
            raise ValueError("Debes enviar exactamente uno: id_huella o documento.")
        return self


class AccesoResponse(BaseModel):
    permitido: bool
    mensaje: str


# -------- Endpoint unificado --------
@router.post("/verificar-acceso", response_model=AccesoResponse)
def verificar_acceso(request: AccesoFlexibleRequest, db: Session = Depends(get_db)):
    """
    Verifica acceso por huella O por documento (cédula).
    - Si viene id_huella: busca Cliente por id_huella.
    - Si viene documento: busca Cliente por documento.
    Reusa AccesoService.verificar_acceso(cliente_id).
    """
    if request.id_huella is not None:
        cliente = cliente_repo.get_by_id_huella(db, id_huella=request.id_huella)
        metodo = "huella"
    else:
        cliente = cliente_repo.get_by_documento(db, documento=request.documento)  # type: ignore[arg-type]
        metodo = "documento"

    if not cliente:
        raise HTTPException(status_code=404, detail=f"Acceso denegado: {metodo} no registrado en el sistema.")

    # Si tu AccesoService acepta tipo_acceso (recomendado):
    return servicio_acceso.verificar_acceso(db, cliente.id, tipo_acceso=metodo)

    # Si NO acepta tipo_acceso aún, usa esta línea en su lugar:
    # return servicio_acceso.verificar_acceso(db, cliente.id)

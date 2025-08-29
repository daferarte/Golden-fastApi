from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from pydantic import BaseModel

from app.db.session import get_db
from app.services.acceso_service import AccesoService
# --- ⭐ 1. Importar el repositorio de cliente ---
# Lo necesitamos para poder buscar al cliente por su id_huella.
from app.repositories.cliente_repository import ClienteRepository

router = APIRouter()
servicio_acceso = AccesoService()

# --- ⭐ 2. El cuerpo de la petición ahora espera un 'id_huella' ---
# Este es el ID que el sensor envía.
class AccesoRequest(BaseModel):
    id_huella: int

class AccesoResponse(BaseModel):
    permitido: bool
    mensaje: str

@router.post("/verificar-acceso", response_model=AccesoResponse)
def verificar_acceso_endpoint(request: AccesoRequest, db: Session = Depends(get_db)):
    """
    Recibe un id_huella desde el dispositivo, busca al cliente correspondiente,
    y luego verifica su acceso usando el servicio de acceso.
    """
    # --- ⭐ 3. Buscar al cliente usando su id_huella ---
    cliente_repo = ClienteRepository()
    cliente_encontrado = cliente_repo.get_by_id_huella(db, id_huella=request.id_huella)

    # Si no se encuentra un cliente con esa huella, se deniega el acceso.
    if not cliente_encontrado:
        # Usamos HTTPException para devolver un error claro, que es mejor práctica.
        raise HTTPException(
            status_code=404, 
            detail="Acceso denegado: Huella no registrada en el sistema."
        )

    # --- ⭐ 4. Llamar al servicio de acceso con el ID de cliente correcto ---
    # Una vez encontrado el cliente, usamos su 'id' principal para la lógica de negocio.
    # De esta forma, no tienes que modificar tu AccesoService.
    resultado = servicio_acceso.verificar_acceso(db, cliente_encontrado.id)
    
    # Esta lógica se mantiene igual.
    if resultado["permitido"]:
        print(f"Acceso concedido para el cliente ID {cliente_encontrado.id} ({cliente_encontrado.nombre}). Abriendo puerta...")

    return resultado

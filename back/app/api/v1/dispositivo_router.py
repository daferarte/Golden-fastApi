# --- Imports existentes ---
from fastapi import APIRouter, HTTPException
from pydantic import BaseModel
from typing import Optional, List

# --- Imports para la base de datos ---
from fastapi import Depends
from sqlalchemy.orm import Session
import base64
from app.db.session import get_db
from app.services.cliente_service import ClienteService

from app.repositories.cliente_repository import ClienteRepository # Necesario para buscar el ID
from app.api import deps

router = APIRouter()
pending_commands = {}

permitir_solo_duenos = deps.RoleChecker(["dueño"])
permitir_staff = deps.get_current_active_user


class ComandoRequest(BaseModel):
    comando: str
    cliente_id: Optional[int] = None
    id_huella: Optional[int] = None # <-- AÑADIDO

# Este endpoint es el que llama tu panel de admin para INICIAR una acción
@router.post("/dispositivo/{device_id}/comando")
async def enviar_comando(device_id: int, request: ComandoRequest, db: Session = Depends(get_db)):
    
    comando_final = request.dict()

    # --- ⭐ CAMBIO 2: Lógica para enriquecer el comando 'update' ---
    # Si el comando es 'update', buscamos al cliente para obtener su id_huella.
    # --- ⭐ CAMBIO 2: Lógica mejorada para el comando 'update' ---
    if request.comando == "update" and request.cliente_id:
        service = ClienteService()
        cliente = service.get_by_id(db, request.cliente_id)
        
        if not cliente:
            raise HTTPException(status_code=404, detail="Cliente no encontrado para comando de actualización")
        
        # --- Lógica de asignación de id_huella ---
        huella_id_para_sensor = cliente.id_huella
        
        # Si el cliente NO tiene un id_huella, le asignamos uno.
        if not huella_id_para_sensor:
            print(f"Cliente ID {cliente.id} no tiene id_huella. Asignando uno nuevo...")
            
            # Instanciamos el repositorio para usar su lógica
            repo = ClienteRepository()
            
            # Buscamos el siguiente ID disponible
            next_id = repo.find_next_available_huella_id(db)
            
            # Asignamos el nuevo ID al cliente y guardamos en la BD
            cliente.id_huella = next_id
            db.commit()
            db.refresh(cliente)
            
            huella_id_para_sensor = cliente.id_huella
            print(f"ID de huella {huella_id_para_sensor} asignado al cliente {cliente.id}.")
        
        # Añadimos el id_huella (existente o recién creado) al comando final
        comando_final['id_huella'] = huella_id_para_sensor
        
    pending_commands[device_id] = comando_final
    return {"mensaje": f"Comando '{request.comando}' preparado para el dispositivo {device_id}"}


# Este endpoint es el que el ESP32 consulta para ver si tiene trabajo
@router.get("/dispositivo/{device_id}/comando")
async def obtener_comando(device_id: int):
    # Usamos .pop para obtener el comando y eliminarlo, evitando que se ejecute dos veces.
    return pending_commands.pop(device_id, {})


@router.post("/dispositivo/{device_id}/confirmar")
async def confirmar_comando(device_id: int, request: BaseModel):
    # La confirmación ya no es necesaria si usamos .pop() en obtener_comando,
    # pero la mantenemos por si la necesitas para logs o futuras acciones.
    return {"mensaje": "Comando procesado"}

@router.get("/clientes/huellas")
def obtener_todas_huellas(db: Session = Depends(get_db)):
    service = ClienteService()
    clientes = service.get_all_with_huella(db)  # lo implementas en tu service
    data = []
    for cliente in clientes:
        if cliente.huella_template:
            data.append({
                "cliente_id": cliente.id,
                "id_huella": cliente.id_huella,
                "template": base64.b64encode(cliente.huella_template).decode("utf-8")
            })
    return data
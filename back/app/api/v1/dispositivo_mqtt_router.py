from fastapi import APIRouter, HTTPException, Depends
from pydantic import BaseModel
from typing import Optional

from sqlalchemy.orm import Session
from app.db.session import get_db
from app.services.cliente_service import ClienteService
from app.repositories.cliente_repository import ClienteRepository

# --- ¡IMPORTANTE! Importamos nuestro cliente MQTT ---
# La ruta "app.mqtt_client" funciona porque FastAPI corre desde el directorio raíz.
from app.mqtt_client import mqtt_client

router = APIRouter()

# El modelo de la petición es el mismo que ya usabas.
class ComandoRequest(BaseModel):
    comando: str
    cliente_id: Optional[int] = None

# ==============================================================================
# ENDPOINT DEDICADO PARA PUBLICAR COMANDOS VÍA MQTT
# ==============================================================================
# Usamos una URL ligeramente diferente para evitar conflictos.
@router.post("/comando_mqtt/{device_id}")
async def enviar_comando_via_mqtt(device_id: int, request: ComandoRequest, db: Session = Depends(get_db)):
    """
    Recibe un comando desde el panel de administración, procesa la lógica
    de negocio y lo publica inmediatamente en el topic MQTT del dispositivo.
    """
    comando_final = request.dict()

    # --- Tu lógica de negocio para 'update' se mantiene intacta ---
    if request.comando == "update" and request.cliente_id:
        service = ClienteService()
        cliente = service.get_by_id(db, request.cliente_id)
        
        if not cliente:
            raise HTTPException(status_code=404, detail="Cliente no encontrado para el comando 'update'")
        
        huella_id_para_sensor = cliente.id_huella
        if not huella_id_para_sensor:
            repo = ClienteRepository()
            next_id = repo.find_next_available_huella_id(db)
            cliente.id_huella = next_id
            db.commit()
            db.refresh(cliente)
            huella_id_para_sensor = cliente.id_huella
        
        comando_final['id_huella'] = huella_id_para_sensor
    
    # --- ⭐ Publicar el comando vía MQTT ---
    topic = f"dispositivo/{device_id}/comandos"
    success = mqtt_client.publish(topic, comando_final)
    
    if success:
        return {"mensaje": f"Comando '{request.comando}' enviado exitosamente al dispositivo {device_id} vía MQTT."}
    else:
        raise HTTPException(status_code=500, detail="Error al enviar el comando. El servicio de mensajería (MQTT) podría no estar disponible.")

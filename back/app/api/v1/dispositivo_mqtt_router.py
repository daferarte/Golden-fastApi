# app/api/v1/dispositivo_mqtt_router.py
from fastapi import APIRouter, HTTPException
from pydantic import BaseModel, Field
from typing import Optional, Any, Dict
from app.mqtt_client import mqtt_client, topic_state, topic_config

router = APIRouter(prefix="/dispositivos", tags=["Dispositivos (MQTT)"])

# --------- Schemas ----------
class CommandIn(BaseModel):
    action: str = Field(..., examples=["open_door", "set_led"])
    payload: Optional[Dict[str, Any]] = Field(default=None, examples=[{"timeout_ms": 3500}])
    timeout: float = 5.0

class StateIn(BaseModel):
    data: Dict[str, Any] = Field(..., examples=[{"online": True}])
    retain: bool = True

class ConfigIn(BaseModel):
    data: Dict[str, Any] = Field(..., examples=[{"finger_scan_mode": "manual_trigger"}])
    retain: bool = True

# --------- Endpoints ----------

@router.post("/{sede}/{device}/cmd")
def send_command(sede: str, device: str, body: CommandIn):
    try:
        ok = mqtt_client.send_command_and_wait_ack(
            sede=sede,
            device=device,
            action=body.action,
            payload=body.payload,
            timeout=body.timeout
        )
        return {"ok": ok}
    except Exception as e:
        raise HTTPException(status_code=502, detail=f"MQTT error: {e}")

@router.post("/{sede}/{device}/state")
def publish_state(sede: str, device: str, body: StateIn):
    topic = topic_state(sede, device)
    ok = mqtt_client.publish_json(topic, body.data, qos=1, retain=body.retain)
    if not ok:
        raise HTTPException(status_code=502, detail="No se pudo publicar state")
    return {"ok": True}

@router.post("/{sede}/{device}/config")
def publish_config(sede: str, device: str, body: ConfigIn):
    topic = topic_config(sede, device)
    ok = mqtt_client.publish_json(topic, body.data, qos=1, retain=body.retain)
    if not ok:
        raise HTTPException(status_code=502, detail="No se pudo publicar config")
    return {"ok": True}

@router.post("/{sede}/{device}/ping")
def ping_device(sede: str, device: str):
    ok = mqtt_client.send_command_and_wait_ack(sede, device, "open_door", {"timeout_ms": 1000}, timeout=3.0)
    return {"ok": ok}

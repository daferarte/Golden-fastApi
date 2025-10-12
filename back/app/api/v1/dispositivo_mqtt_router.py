# app/api/v1/dispositivo_mqtt_router.py
from fastapi import APIRouter, HTTPException
from pydantic import BaseModel, Field, model_validator
from typing import Optional, Any, Dict

from app.mqtt_client import mqtt_client, topic_state, topic_config

router = APIRouter(prefix="/dispositivos", tags=["Dispositivos (MQTT)"])

# =======================
#    Schemas / Models
# =======================
class CommandIn(BaseModel):
    """
    Comando a un dispositivo. El 'action' lo interpreta el firmware.
    Puedes enviar cliente_id e id_huella a nivel raíz (opción 1 / legacy) o dentro de payload.
    """
    action: str = Field(..., examples=["open_door", "update", "set_led"])
    # Opción 1 (legacy / plano):
    cliente_id: Optional[int] = Field(default=None, description="Requerido para 'update'")
    id_huella: Optional[int]  = Field(default=None, description="Requerido para 'update'")
    # Payload libre (opción 2):
    payload: Optional[Dict[str, Any]] = Field(
        default=None,
        examples=[{"timeout_ms": 3500}, {"color": "green"}, {"cliente_id": 236, "id_huella": 1}]
    )
    timeout: float = Field(
        5.0, ge=0.1, le=60,
        description="Tiempo máximo (segundos) para esperar el ACK del dispositivo."
    )

    @model_validator(mode="after")
    def validate_update_requires_ids(self):
        if self.action == "update":
            # Acepta en raíz o dentro de payload
            cid = self.cliente_id if self.cliente_id is not None else (self.payload or {}).get("cliente_id")
            fid = self.id_huella if self.id_huella is not None else (self.payload or {}).get("id_huella")
            if cid is None or fid is None:
                raise ValueError("Para 'update' se requieren 'cliente_id' e 'id_huella' (en raíz o en payload).")
        return self


class StateIn(BaseModel):
    """Publicación de 'state' del dispositivo (retain recomendado en True)."""
    data: Dict[str, Any] = Field(..., examples=[{"online": True, "firmware": "1.0.0", "rssi": -55}])
    retain: bool = Field(True, description="Si True, el broker retiene el último state para nuevos suscriptores.")


class ConfigIn(BaseModel):
    """Publicación de 'config' deseada del dispositivo (retain recomendado)."""
    data: Dict[str, Any] = Field(
        ...,
        examples=[{"finger_scan_mode": "manual_trigger", "led_defaults": {"success": "green", "error": "red"}}]
    )
    retain: bool = Field(True, description="Si True, el broker retiene la última config para nuevos suscriptores.")


class OkOut(BaseModel):
    ok: bool


# =======================
#       Endpoints
# =======================

@router.post("/{sede}/{device}/cmd", response_model=OkOut, summary="Enviar comando y esperar ACK")
def send_command(sede: str, device: str, body: CommandIn):
    """
    Publica un comando en `devices/{sede}/{device}/cmd` y espera el ACK en `.../cmd/ack`.
    - Publica el JSON plano con `action` y, si existen, `cliente_id`/`id_huella` a nivel raíz.
    - También fusiona cualquier `payload` adicional.
    """
    try:
        # Construimos el payload final que se publicará:
        #   - action siempre
        #   - cliente_id e id_huella (si vienen en raíz) para opción 1
        #   - merge con payload (si trae keys, también se incluyen)
        out_payload: Dict[str, Any] = {"action": body.action}

        if body.payload:
            out_payload.update(body.payload)

        if body.cliente_id is not None:
            out_payload["cliente_id"] = body.cliente_id
        if body.id_huella is not None:
            out_payload["id_huella"] = body.id_huella

        ok = mqtt_client.send_command_and_wait_ack(
            sede=sede,
            device=device,
            action=body.action,
            payload=out_payload,   # <-- publicamos TODO junto (incluye cliente_id/id_huella si los enviaste)
            timeout=body.timeout
        )
        return OkOut(ok=ok)
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=502, detail=f"MQTT error: {e!s}")


@router.post("/{sede}/{device}/state", response_model=OkOut, summary="Publicar state (retain opcional)")
def publish_state(sede: str, device: str, body: StateIn):
    topic = topic_state(sede, device)
    ok = mqtt_client.publish_json(topic, body.data, qos=1, retain=body.retain)
    if not ok:
        raise HTTPException(status_code=502, detail="No se pudo publicar state")
    return OkOut(ok=True)


@router.post("/{sede}/{device}/config", response_model=OkOut, summary="Publicar config (retain recomendado)")
def publish_config(sede: str, device: str, body: ConfigIn):
    topic = topic_config(sede, device)
    ok = mqtt_client.publish_json(topic, body.data, qos=1, retain=body.retain)
    if not ok:
        raise HTTPException(status_code=502, detail="No se pudo publicar config")
    return OkOut(ok=True)


@router.post("/{sede}/{device}/ping", response_model=OkOut, summary="Ping de comando (abre puerta)")
def ping_device(sede: str, device: str):
    try:
        ok = mqtt_client.send_command_and_wait_ack(
            sede, device, "open_door",
            {"timeout_ms": 1000},
            timeout=3.0
        )
        return OkOut(ok=ok)
    except Exception as e:
        raise HTTPException(status_code=502, detail=f"MQTT error: {e!s}")

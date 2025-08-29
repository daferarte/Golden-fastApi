from fastapi import APIRouter, Depends, HTTPException
from app.utils.esp32_client import ESP32Client

router = APIRouter()
client = ESP32Client()

@router.post('/open_gate')
async def open_gate(cliente_id: int):
    # try:
    #     res = await client.send_command('command', {'cmd': 'open_gate', 'cliente_id': cliente_id})
    #     return res
    # except Exception as e:
    #     raise HTTPException(status_code=502, detail=str(e))
    return True

@router.get('/status')
async def esp_status():
    try:
        return await client.get_status()
    except Exception as e:
        raise HTTPException(status_code=502, detail=str(e))
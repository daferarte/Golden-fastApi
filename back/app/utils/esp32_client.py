import httpx
from app.core.config import settings

class ESP32Client:
    def __init__(self, base_url: str | None = None):
        self.base_url = base_url or settings.esp32_base_url

    async def send_command(self, endpoint: str, payload: dict):
        url = f"{self.base_url}/{endpoint.lstrip('/')}"
        async with httpx.AsyncClient(timeout=10) as client:
            r = await client.post(url, json=payload)
            r.raise_for_status()
            return r.json()

    async def get_status(self):
        async with httpx.AsyncClient(timeout=5) as client:
            r = await client.get(self.base_url + "/status")
            r.raise_for_status()
            return r.json()

# Uso: client = ESP32Client() ; await client.send_command('command', {'cmd': 'open_gate', 'cliente_id': 12})
from typing import List
from fastapi import WebSocket
import json

class EventBroadcaster:
    def __init__(self):
        self.active_connections: List[WebSocket] = []

    async def connect(self, websocket: WebSocket):
        await websocket.accept()
        self.active_connections.append(websocket)
        print(f"✅ Cliente conectado ({len(self.active_connections)} total)")

    def disconnect(self, websocket: WebSocket):
        self.active_connections.remove(websocket)
        print(f"❌ Cliente desconectado ({len(self.active_connections)} restantes)")

    async def broadcast(self, data: dict):
        message = json.dumps(data)
        for ws in list(self.active_connections):
            try:
                await ws.send_text(message)
            except Exception:
                self.disconnect(ws)

broadcaster = EventBroadcaster()

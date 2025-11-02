# app/api/ws_events.py
from fastapi import APIRouter, WebSocket, WebSocketDisconnect
from app.services.event_broadcast import broadcaster

router = APIRouter(prefix="/ws", tags=["WebSocket Events"])

@router.websocket("/events")
async def websocket_events(ws: WebSocket):
    await broadcaster.connect(ws)
    try:
        while True:
            await ws.receive_text()  # opcional (mantiene conexión)
    except WebSocketDisconnect:
        broadcaster.disconnect(ws)

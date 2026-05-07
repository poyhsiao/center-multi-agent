"""WebSocket endpoint for real-time agent communication."""
from fastapi import APIRouter, WebSocket, WebSocketDisconnect

from app.core.logging import get_logger

logger = get_logger(__name__)
router = APIRouter()


@router.websocket("/ws")
async def websocket_endpoint(websocket: WebSocket):
    """WebSocket endpoint for real-time communication."""
    await websocket.accept()
    client_id = websocket.client.host if websocket.client else "unknown"
    logger.info("websocket_connected", client_id=client_id)

    try:
        while True:
            data = await websocket.receive_text()
            logger.info("websocket_message_received", client_id=client_id, data=data)
            await websocket.send_text(f"Echo: {data}")
    except WebSocketDisconnect:
        logger.info("websocket_disconnected", client_id=client_id)
    except Exception as e:
        logger.error("websocket_error", client_id=client_id, error=str(e))

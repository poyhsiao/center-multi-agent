"""WebSocket Connection Manager - Bidirectional communication."""

import asyncio
from collections import defaultdict
from typing import Any

from fastapi import WebSocket


class WebSocketManager:
    """Manage WebSocket connections for bidirectional communication."""

    def __init__(self):
        self._channels: dict[str, list[WebSocket]] = defaultdict(list)
        self._lock = asyncio.Lock()

    async def connect(self, websocket: WebSocket, user_id: str) -> None:
        """Accept and register a WebSocket connection."""
        await websocket.accept()
        async with self._lock:
            self._channels[user_id].append(websocket)

    async def disconnect(self, websocket: WebSocket, user_id: str) -> None:
        """Remove a WebSocket connection."""
        async with self._lock:
            if user_id in self._channels:
                self._channels[user_id] = [
                    ws for ws in self._channels[user_id]
                    if ws != websocket
                ]
                if not self._channels[user_id]:
                    del self._channels[user_id]

    async def send_to_user(self, user_id: str, data: dict) -> bool:
        """Send data to specific user's WebSocket."""
        if user_id not in self._channels:
            return False

        sent = False
        for websocket in self._channels[user_id]:
            try:
                await websocket.send_json(data)
                sent = True
            except Exception:
                pass
        return sent

    async def broadcast_to_user(self, user_id: str, data: dict) -> None:
        """Broadcast message to specific user."""
        await self.send_to_user(user_id, data)

    async def broadcast_all(self, data: dict) -> None:
        """Broadcast message to all connected users."""
        for user_id in list(self._channels.keys()):
            await self.send_to_user(user_id, data)


# Global WebSocket manager instance
websocket_manager = WebSocketManager()
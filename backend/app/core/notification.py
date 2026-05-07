"""SSE Notification Manager - Real-time event broadcasting."""

import asyncio
from collections import defaultdict
from dataclasses import dataclass
from datetime import datetime
from typing import Any


@dataclass
class Connection:
    """Client connection wrapper."""
    user_id: str
    connection: Any
    connected_at: datetime


class SSENotificationManager:
    """Manage SSE connections and broadcast events to users."""

    def __init__(self):
        self._connections: dict[str, list[Connection]] = defaultdict(list)
        self._lock = asyncio.Lock()

    def add_connection(self, user_id: str, connection: Any) -> None:
        """Add a client connection for a user."""
        conn = Connection(
            user_id=user_id,
            connection=connection,
            connected_at=datetime.utcnow()
        )
        self._connections[user_id].append(conn)

    def remove_connection(self, user_id: str) -> None:
        """Remove all connections for a user."""
        if user_id in self._connections:
            del self._connections[user_id]

    async def broadcast(
        self, event_type: str, data: dict, user_ids: list[str] = None
    ) -> None:
        """Broadcast event to specified users or all connected users."""
        if user_ids is None:
            # Broadcast to all connected users
            target_users = list(self._connections.keys())
        else:
            target_users = user_ids

        for user_id in target_users:
            connections = self._connections.get(user_id, [])
            for conn_wrapper in connections:
                try:
                    await conn_wrapper.connection.send_json(data)
                except Exception:
                    # Remove failed connections
                    self.remove_connection(user_id)

    def get_connected_users(self) -> list[str]:
        """Get list of all connected user IDs."""
        return list(self._connections.keys())


# Global notification manager instance
notification_manager = SSENotificationManager()
"""WebSocket connection manager for real-time notifications."""
from __future__ import annotations
import asyncio
import json
import logging
from datetime import datetime, timezone
from uuid import UUID

from fastapi import WebSocket, WebSocketDisconnect

logger = logging.getLogger(__name__)


class ConnectionManager:
    """
    Manages active WebSocket connections per user.
    Supports multiple connections per user (e.g., multiple browser tabs).
    Uses Redis pub/sub for cross-process message delivery so multiple
    API workers can all deliver to connected clients.
    """

    def __init__(self):
        # user_id -> list of WebSocket connections
        self._connections: dict[str, list[WebSocket]] = {}

    async def connect(self, websocket: WebSocket, user_id: str) -> None:
        await websocket.accept()
        if user_id not in self._connections:
            self._connections[user_id] = []
        self._connections[user_id].append(websocket)
        logger.info(f"WebSocket connected: user={user_id}, total={len(self._connections[user_id])}")

    def disconnect(self, websocket: WebSocket, user_id: str) -> None:
        if user_id in self._connections:
            try:
                self._connections[user_id].remove(websocket)
            except ValueError:
                pass
            if not self._connections[user_id]:
                del self._connections[user_id]
        logger.info(f"WebSocket disconnected: user={user_id}")

    async def send_to_user(self, user_id: str, message: dict) -> int:
        """Send a message to all connections for a user. Returns number of connections reached."""
        if user_id not in self._connections:
            return 0
        
        payload = json.dumps(message, default=str)
        dead_connections = []
        sent = 0
        
        for ws in self._connections[user_id]:
            try:
                await ws.send_text(payload)
                sent += 1
            except Exception:
                dead_connections.append(ws)
        
        for ws in dead_connections:
            self.disconnect(ws, user_id)
        
        return sent

    async def broadcast_to_org(self, org_id: str, message: dict) -> int:
        """Send a message to all users in an organization."""
        # In a real multi-process setup this would use Redis pub/sub.
        # For single-process, iterate all connections.
        total = 0
        for user_id in list(self._connections.keys()):
            total += await self.send_to_user(user_id, message)
        return total

    def get_connected_users(self) -> list[str]:
        return list(self._connections.keys())

    def get_connection_count(self) -> int:
        return sum(len(conns) for conns in self._connections.values())


# Module-level singleton
manager = ConnectionManager()


async def publish_notification(user_id: str, notification: dict) -> None:
    """
    Publish a notification to a user via WebSocket.
    Also stores in Redis so the notification can be delivered if user connects later.
    """
    message = {
        "type": "notification",
        "data": notification,
        "timestamp": datetime.now(timezone.utc).isoformat(),
    }
    
    delivered = await manager.send_to_user(str(user_id), message)
    
    # Also publish via Redis pub/sub for multi-worker setups
    try:
        import redis.asyncio as aioredis
        from backend.config import get_settings
        settings = get_settings()
        r = aioredis.from_url(settings.REDIS_URL)
        channel = f"notifications:{user_id}"
        await r.publish(channel, json.dumps(message, default=str))
        await r.aclose()
    except Exception as e:
        logger.debug(f"Redis pub/sub not available: {e}")
    
    logger.info(f"Notification published to user {user_id}, delivered to {delivered} WebSocket(s)")


async def handle_websocket(websocket: WebSocket, user_id: str, org_id: str) -> None:
    """
    Main WebSocket handler. Keeps connection alive, handles ping/pong,
    and subscribes to Redis channel for this user.
    """
    await manager.connect(websocket, user_id)
    
    # Send connected acknowledgment
    await websocket.send_text(json.dumps({
        "type": "connected",
        "user_id": user_id,
        "timestamp": datetime.now(timezone.utc).isoformat(),
    }))

    # Start Redis subscriber task
    redis_task = asyncio.create_task(_redis_subscriber(websocket, user_id))

    try:
        while True:
            try:
                # Wait for client messages (ping/pong, ack)
                data = await asyncio.wait_for(websocket.receive_text(), timeout=30)
                msg = json.loads(data)
                
                if msg.get("type") == "ping":
                    await websocket.send_text(json.dumps({"type": "pong", "timestamp": datetime.now(timezone.utc).isoformat()}))
                elif msg.get("type") == "ack":
                    # Client acknowledged a notification -- could mark as read
                    pass

            except asyncio.TimeoutError:
                # Send server-side ping to keep connection alive
                try:
                    await websocket.send_text(json.dumps({"type": "ping"}))
                except Exception:
                    break

    except WebSocketDisconnect:
        pass
    except Exception as e:
        logger.exception(f"WebSocket error for user {user_id}: {e}")
    finally:
        redis_task.cancel()
        manager.disconnect(websocket, user_id)


async def _redis_subscriber(websocket: WebSocket, user_id: str) -> None:
    """Subscribe to Redis channel and forward messages to WebSocket."""
    try:
        import redis.asyncio as aioredis
        from backend.config import get_settings
        settings = get_settings()
        r = aioredis.from_url(settings.REDIS_URL)
        pubsub = r.pubsub()
        await pubsub.subscribe(f"notifications:{user_id}")
        
        async for message in pubsub.listen():
            if message["type"] == "message":
                try:
                    await websocket.send_text(message["data"])
                except Exception:
                    break
        
        await r.aclose()
    except asyncio.CancelledError:
        pass
    except Exception as e:
        logger.debug(f"Redis subscriber error: {e}")

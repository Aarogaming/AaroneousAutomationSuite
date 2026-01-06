import asyncio
import json
from typing import Any, Dict, Set
from fastapi import FastAPI, WebSocket, WebSocketDisconnect
from loguru import logger


class WebSocketManager:
    """
    Manages WebSocket connections for real-time event streaming.
    """

    def __init__(self) -> None:
        self.active_connections: Set[WebSocket] = set()

    async def connect(self, websocket: WebSocket) -> None:
        await websocket.accept()
        self.active_connections.add(websocket)
        logger.info(f"WebSocket client connected. Total: {len(self.active_connections)}")

    def disconnect(self, websocket: WebSocket) -> None:
        if websocket in self.active_connections:
            self.active_connections.remove(websocket)
            logger.info(f"WebSocket client disconnected. Total: {len(self.active_connections)}")

    async def broadcast(self, message: Dict[str, Any]) -> None:
        if not self.active_connections:
            return

        message_str = json.dumps(message)
        disconnected: Set[WebSocket] = set()

        for connection in self.active_connections:
            try:
                await connection.send_text(message_str)
            except Exception:
                disconnected.add(connection)

        for conn in disconnected:
            self.disconnect(conn)


# Global manager instance
manager = WebSocketManager()


def setup_websocket_routes(app: FastAPI) -> None:
    """Register WebSocket endpoints on the provided FastAPI app."""

    @app.websocket("/ws/events")
    async def websocket_endpoint(websocket: WebSocket) -> None:
        await manager.connect(websocket)
        try:
            while True:
                # Keep connection alive and wait for messages if needed
                data = await websocket.receive_text()
                # Echo or handle incoming messages
                await websocket.send_text(f"Message received: {data}")
        except WebSocketDisconnect:
            manager.disconnect(websocket)
        except Exception as e:
            logger.error(f"WebSocket error: {e}")
            manager.disconnect(websocket)

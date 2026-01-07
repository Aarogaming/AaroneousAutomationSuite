import asyncio
import json
import os
from typing import Any, Dict, Set
from fastapi import FastAPI, WebSocket, WebSocketDisconnect, HTTPException
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

    async def endpoint(websocket: WebSocket) -> None:
        auth_token = os.getenv("AAS_API_TOKEN")
        if auth_token:
            provided = websocket.headers.get("x-aas-token")
            if not provided:
                auth_header = websocket.headers.get("authorization", "")
                if auth_header.lower().startswith("bearer "):
                    provided = auth_header.split(" ", 1)[1]
            if not provided:
                try:
                    provided = websocket.query_params.get("token")
                except Exception:
                    provided = None
            if provided != auth_token:
                await websocket.close(code=4401)
                return

        await manager.connect(websocket)
        try:
            while True:
                data = await websocket.receive_text()
                await websocket.send_text(f"Message received: {data}")
        except WebSocketDisconnect:
            manager.disconnect(websocket)
        except Exception as e:
            logger.error(f"WebSocket error: {e}")
            manager.disconnect(websocket)

    # Primary events socket
    app.websocket("/ws/events")(endpoint)
    # Alias for simpler clients
    app.websocket("/ws")(endpoint)

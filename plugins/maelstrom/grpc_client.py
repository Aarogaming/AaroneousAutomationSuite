"""
gRPC Client for Maelstrom Communication

This module provides the gRPC client for communicating with Project Maelstrom
when it acts as a server, or for making outbound calls.

The primary flow is:
1. AAS Hub hosts gRPC server (BridgeService)
2. Maelstrom connects as client
3. This client is for optional reverse communication

Usage:
    client = await MaelstromClient.connect("localhost:50052")
    response = await client.execute_command("MOVE", {"x": 100, "y": 200})
    await client.close()
"""

import asyncio
import json
from typing import Dict, Any, Optional, AsyncIterator
from dataclasses import dataclass
from loguru import logger

try:
    import grpc
    from core.ipc.protos import bridge_pb2, bridge_pb2_grpc
    GRPC_AVAILABLE = True
except ImportError:
    GRPC_AVAILABLE = False
    logger.warning("gRPC not available. Install grpcio for full Maelstrom support.")


@dataclass
class CommandResult:
    """Result of a Maelstrom command execution."""
    success: bool
    message: str
    data: Optional[Dict[str, Any]] = None


class MaelstromClient:
    """
    Async gRPC client for communicating with Project Maelstrom.
    
    This client uses the same bridge.proto schema for bidirectional
    communication between AAS Hub and Maelstrom.
    """
    
    def __init__(self, address: str = "localhost:50052"):
        """
        Initialize client (does not connect yet).
        
        Args:
            address: Maelstrom gRPC server address (host:port)
        """
        self._address = address
        self._channel: Optional['grpc.aio.Channel'] = None
        self._stub: Optional['bridge_pb2_grpc.BridgeStub'] = None
        self._connected = False
    
    @classmethod
    async def connect(cls, address: str = "localhost:50052") -> 'MaelstromClient':
        """
        Factory method to create and connect a client.
        
        Args:
            address: Maelstrom gRPC server address
            
        Returns:
            Connected MaelstromClient instance
        """
        client = cls(address)
        await client._connect()
        return client
    
    async def _connect(self) -> bool:
        """Establish gRPC connection."""
        if not GRPC_AVAILABLE:
            logger.error("gRPC not available. Cannot connect to Maelstrom.")
            return False
        
        try:
            logger.info(f"Connecting to Maelstrom at {self._address}...")
            
            self._channel = grpc.aio.insecure_channel(self._address)
            self._stub = bridge_pb2_grpc.BridgeStub(self._channel)
            
            # Test connection with a config request
            await asyncio.wait_for(
                self._stub.GetConfig(bridge_pb2.ConfigRequest(key="version")),
                timeout=5.0
            )
            
            self._connected = True
            logger.success(f"Connected to Maelstrom at {self._address}")
            return True
            
        except asyncio.TimeoutError:
            logger.error(f"Connection to Maelstrom timed out: {self._address}")
            return False
        except Exception as e:
            logger.error(f"Failed to connect to Maelstrom: {e}")
            return False
    
    async def close(self) -> None:
        """Close the gRPC connection."""
        if self._channel:
            await self._channel.close()
            self._connected = False
            logger.info("Disconnected from Maelstrom")
    
    @property
    def is_connected(self) -> bool:
        """Check if client is connected."""
        return self._connected and self._channel is not None
    
    async def execute_command(
        self, 
        command_type: str, 
        payload: Optional[Dict[str, Any]] = None
    ) -> CommandResult:
        """
        Execute a command on Maelstrom.
        
        Args:
            command_type: Type of command (e.g., MOVE, CLICK, SEND_KEY)
            payload: Command parameters as dict
            
        Returns:
            CommandResult with success status and response
        """
        if not self.is_connected or not self._stub:
            return CommandResult(False, "Not connected to Maelstrom")
        
        try:
            payload_json = json.dumps(payload) if payload else "{}"
            
            request = bridge_pb2.CommandRequest(
                command_type=command_type,
                payload=payload_json
            )
            
            response = await self._stub.ExecuteCommand(request)
            
            return CommandResult(
                success=response.success,
                message=response.message
            )
            
        except Exception as e:
            logger.error(f"Command execution failed: {e}")
            return CommandResult(False, str(e))
    
    async def get_config(self, key: str) -> Optional[str]:
        """
        Get a configuration value from Maelstrom.
        
        Args:
            key: Configuration key
            
        Returns:
            Configuration value or None if not found
        """
        if not self.is_connected or not self._stub:
            return None
        
        try:
            response = await self._stub.GetConfig(
                bridge_pb2.ConfigRequest(key=key)
            )
            return response.configs.get(key)
        except Exception as e:
            logger.error(f"Failed to get config '{key}': {e}")
            return None
    
    async def set_config(
        self, 
        key: str, 
        value: str, 
        value_type: str = "string",
        is_secret: bool = False
    ) -> bool:
        """
        Set a configuration value on Maelstrom.
        
        Args:
            key: Configuration key
            value: Configuration value
            value_type: Type hint (string, int, bool, json)
            is_secret: Whether this is a secret value
            
        Returns:
            True if successful
        """
        if not self.is_connected or not self._stub:
            return False
        
        try:
            response = await self._stub.SetConfig(
                bridge_pb2.SetConfigRequest(
                    key=key,
                    value=value,
                    value_type=value_type,
                    is_secret=is_secret
                )
            )
            return response.success
        except Exception as e:
            logger.error(f"Failed to set config '{key}': {e}")
            return False
    
    async def stream_snapshots(
        self, 
        interval_ms: int = 100
    ) -> AsyncIterator[Dict[str, Any]]:
        """
        Stream game state snapshots from Maelstrom.
        
        Args:
            interval_ms: Requested snapshot interval in milliseconds
            
        Yields:
            Game state snapshot dictionaries
        """
        if not self.is_connected or not self._stub:
            return
        
        try:
            request = bridge_pb2.SnapshotRequest(interval_ms=interval_ms)
            
            async for snapshot in self._stub.StreamSnapshots(request):
                try:
                    data = json.loads(snapshot.data)
                    data["_timestamp"] = snapshot.timestamp
                    yield data
                except json.JSONDecodeError:
                    yield {"raw": snapshot.data, "_timestamp": snapshot.timestamp}
                    
        except Exception as e:
            logger.error(f"Snapshot stream error: {e}")


# === Convenience Functions ===

async def send_game_command(
    command: str, 
    params: Optional[Dict[str, Any]] = None,
    address: str = "localhost:50052"
) -> CommandResult:
    """
    One-shot command execution to Maelstrom.
    
    Use this for simple commands that don't need persistent connection.
    
    Args:
        command: Command type
        params: Command parameters
        address: Maelstrom server address
        
    Returns:
        CommandResult
    """
    client = MaelstromClient(address)
    try:
        if await client._connect():
            return await client.execute_command(command, params)
        return CommandResult(False, "Failed to connect")
    finally:
        await client.close()


# === Game-Specific Command Helpers ===

class GameCommands:
    """High-level game command interface."""
    
    def __init__(self, client: MaelstromClient):
        self._client = client
    
    async def click(self, x: int, y: int, button: str = "left") -> CommandResult:
        """Click at screen coordinates."""
        return await self._client.execute_command("CLICK", {
            "x": x, "y": y, "button": button
        })
    
    async def move(self, x: float, y: float, z: float = 0) -> CommandResult:
        """Move character to world coordinates."""
        return await self._client.execute_command("MOVE", {
            "x": x, "y": y, "z": z
        })
    
    async def send_key(self, key: str, duration: float = 0.1) -> CommandResult:
        """Send a keypress."""
        return await self._client.execute_command("SEND_KEY", {
            "key": key, "duration": duration
        })
    
    async def send_text(self, text: str) -> CommandResult:
        """Type text string."""
        return await self._client.execute_command("SEND_TEXT", {
            "text": text
        })
    
    async def screenshot(self) -> CommandResult:
        """Capture game screenshot."""
        return await self._client.execute_command("SCREENSHOT", {})
    
    async def get_state(self) -> CommandResult:
        """Get current game state."""
        return await self._client.execute_command("GET_STATE", {})

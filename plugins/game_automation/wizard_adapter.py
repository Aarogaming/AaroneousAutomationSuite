"""
Wizard101 Adapter - IPC Bridge Interface for Game Client

This adapter provides the communication layer between the AAS Hub
and Project Maelstrom's C# game client via gRPC.

Commands are sent through the IPC bridge and executed by Maelstrom,
which has direct access to the Wizard101 process.
"""

from typing import Dict, Any, Optional
from loguru import logger
import asyncio


class Wizard101Adapter:
    """
    Adapter for Wizard101 game client interaction.
    
    Communicates with Project Maelstrom (C#) via gRPC IPC to execute
    game commands like movement, keypresses, and state queries.
    
    All commands are routed through the Hub's IPC bridge, which
    handles the actual gRPC communication.
    """
    
    # Command type constants (must match bridge.proto)
    CMD_MOVE_TO = "MOVE_TO"
    CMD_SEND_KEY = "SEND_KEY"
    CMD_GET_POSITION = "GET_POSITION"
    CMD_GET_STATE = "GET_STATE"
    CMD_INTERACT = "INTERACT"
    
    # Key code mappings
    KEYCODES = {
        'W': 0x57, 'A': 0x41, 'S': 0x53, 'D': 0x44,
        'X': 0x58, 'Z': 0x5A, 'B': 0x42, 'E': 0x45,
        'Q': 0x51, 'R': 0x52, 'F': 0x46, 'C': 0x43,
        'SPACE': 0x20, 'ENTER': 0x0D, 'ESC': 0x1B,
    }
    
    def __init__(self, hub: Any = None):
        """
        Initialize the Wizard101 adapter.
        
        Args:
            hub: Reference to the AAS Hub for IPC access
        """
        self.hub = hub
        self._connected = False
        self._last_position = None
        
    async def _send_command(
        self, 
        command_type: str, 
        payload: Dict[str, Any]
    ) -> Dict[str, Any]:
        """
        Send a command to Maelstrom via IPC bridge.
        
        Args:
            command_type: Type of command (MOVE_TO, SEND_KEY, etc.)
            payload: Command-specific data
            
        Returns:
            Response from Maelstrom with success status
        """
        try:
            # Check if IPC bridge is available
            if not self.hub or not hasattr(self.hub, 'ipc_bridge'):
                logger.warning("IPC bridge not available - using mock response")
                return await self._mock_command(command_type, payload)
            
            # Build command message
            message = {
                "command_type": command_type,
                "payload": payload,
            }
            
            # Send through IPC bridge
            response = await self.hub.ipc_bridge.execute_command(message)
            return response
            
        except Exception as e:
            logger.error(f"Command failed: {command_type} - {e}")
            return {"success": False, "error": str(e)}
    
    async def _mock_command(
        self, 
        command_type: str, 
        payload: Dict[str, Any]
    ) -> Dict[str, Any]:
        """
        Mock command execution for testing without Maelstrom.
        """
        logger.debug(f"[MOCK] Executing {command_type}: {payload}")
        await asyncio.sleep(0.1)  # Simulate latency
        
        if command_type == self.CMD_GET_POSITION:
            return {
                "success": True,
                "data": {"x": 0.0, "y": 0.0, "z": 0.0}
            }
        
        return {"success": True, "mock": True}
    
    # === Public API ===
    
    async def goto(
        self, 
        x: float, 
        y: float, 
        z: Optional[float] = None
    ) -> Dict[str, Any]:
        """
        Move character to target coordinates.
        
        Uses Maelstrom's pathfinding to navigate to the target.
        
        Args:
            x: Target X coordinate
            y: Target Y coordinate
            z: Optional Z coordinate (height)
            
        Returns:
            Success status and final position
        """
        payload = {"x": x, "y": y}
        if z is not None:
            payload["z"] = z
            
        result = await self._send_command(self.CMD_MOVE_TO, payload)
        
        if result.get("success"):
            self._last_position = {"x": x, "y": y, "z": z}
            logger.debug(f"Moved to ({x}, {y}, {z})")
        
        return result
    
    async def send_key(
        self, 
        key: str, 
        duration: float = 0.1
    ) -> Dict[str, Any]:
        """
        Send a keypress to the game client.
        
        Args:
            key: Key name (W, A, S, D, X, etc.)
            duration: How long to hold the key (seconds)
            
        Returns:
            Success status
        """
        key_upper = key.upper()
        keycode = self.KEYCODES.get(key_upper, ord(key_upper) if len(key) == 1 else 0)
        
        payload = {
            "key": key_upper,
            "keycode": keycode,
            "duration": duration
        }
        
        result = await self._send_command(self.CMD_SEND_KEY, payload)
        
        if result.get("success"):
            logger.debug(f"Sent key '{key}' for {duration}s")
        
        return result
    
    async def get_position(self) -> Dict[str, Any]:
        """
        Get current character position from game state.
        
        Returns:
            Current position {x, y, z} or error
        """
        result = await self._send_command(self.CMD_GET_POSITION, {})
        
        if result.get("success") and result.get("data"):
            self._last_position = result["data"]
        
        return result
    
    async def interact(self) -> Dict[str, Any]:
        """
        Press interact key (X) at current location.
        
        Used for:
        - Entering dungeons/areas
        - Talking to NPCs
        - Collecting items
        """
        return await self.send_key('X', 0.2)
    
    async def get_game_state(self) -> Dict[str, Any]:
        """
        Get full game state snapshot from Maelstrom.
        
        Returns comprehensive state including:
        - Player position
        - Health/Mana
        - Combat state
        - Zone information
        """
        return await self._send_command(self.CMD_GET_STATE, {})
    
    def get_last_position(self) -> Optional[Dict[str, float]]:
        """Get cached last known position."""
        return self._last_position
    
    @property
    def is_connected(self) -> bool:
        """Check if adapter has active connection to Maelstrom."""
        return self._connected

"""
Game Automation Plugin - Project Maelstrom Integration

This plugin provides a unified interface for Wizard101 game automation,
bridging the AAS Hub with Project Maelstrom's C# client via gRPC IPC.

Migrated Libraries:
- Automatus-v2: Bot framework with locomotion and pathfinding
- Arcane: Game data parser
- Deimos: Wizard101 scripting language port

Task References:
- AAS-012: AutoWizard101 Migration
- AAS-013: Deimos-Wizard101 Port  
- AAS-014: DanceBot Integration
"""

from typing import Dict, Any, Optional, List
from loguru import logger
import asyncio
import json

from core.plugin_base import PluginBase
from core.config import AASConfig


class GameAutomationPlugin(PluginBase):
    """
    Main plugin class for Wizard101 game automation.
    
    Provides:
    - Locomotion control (pathfinding, movement)
    - Command execution via IPC bridge to Maelstrom
    - Route management for automated navigation
    """
    
    version = "0.1.0"
    
    def __init__(self, config: AASConfig, hub: Any):
        super().__init__("game_automation", config, hub)
        self._locomotion = None
        self._wizard_adapter = None
        self._routes: Dict[str, List[Dict[str, float]]] = {}
        self._current_position: Optional[Dict[str, float]] = None
        
    async def setup(self) -> bool:
        """Initialize game automation components."""
        try:
            logger.info("Initializing Game Automation Plugin...")
            
            # Initialize locomotion controller
            from .locomotion import LocomotionController
            self._locomotion = LocomotionController(
                wizard_speed=getattr(self.config, 'wizard_speed', 580.0),
                logging_enabled=getattr(self.config, 'logging_enabled', True)
            )
            
            # Initialize Wizard101 adapter for IPC commands
            from .wizard_adapter import Wizard101Adapter
            self._wizard_adapter = Wizard101Adapter(hub=self.hub)
            
            # Load routes from artifacts
            await self._load_routes()
            
            # Register IPC command handlers
            await self._register_ipc_handlers()
            
            logger.success("Game Automation Plugin initialized successfully")
            return True
            
        except Exception as e:
            logger.error(f"Failed to initialize Game Automation Plugin: {e}")
            return False
    
    async def shutdown(self) -> bool:
        """Clean up resources."""
        try:
            logger.info("Shutting down Game Automation Plugin...")
            self._locomotion = None
            self._wizard_adapter = None
            return True
        except Exception as e:
            logger.error(f"Error during shutdown: {e}")
            return False
    
    async def _load_routes(self):
        """Load predefined routes from artifacts/routes/"""
        import os
        routes_dir = os.path.join("artifacts", "routes")
        if os.path.exists(routes_dir):
            for filename in os.listdir(routes_dir):
                if filename.endswith('.json'):
                    route_name = filename.replace('.json', '')
                    with open(os.path.join(routes_dir, filename), 'r') as f:
                        self._routes[route_name] = json.load(f)
                    logger.debug(f"Loaded route: {route_name}")
    
    async def _register_ipc_handlers(self):
        """Register command handlers with the IPC bridge."""
        if hasattr(self.hub, 'ipc_bridge'):
            handlers = {
                'game.move_to': self.handle_move_to,
                'game.follow_route': self.handle_follow_route,
                'game.send_key': self.handle_send_key,
                'game.get_position': self.handle_get_position,
                'game.list_routes': self.handle_list_routes,
            }
            for cmd, handler in handlers.items():
                self.hub.ipc_bridge.register_handler(cmd, handler)
                logger.debug(f"Registered IPC handler: {cmd}")
    
    # === IPC Command Handlers ===
    
    async def handle_move_to(self, x: float, y: float, z: Optional[float] = None) -> Dict[str, Any]:
        """
        Move the character to specified coordinates.
        
        Args:
            x: Target X coordinate
            y: Target Y coordinate
            z: Optional Z coordinate (height)
        """
        if not self._wizard_adapter:
            return {"success": False, "error": "Wizard adapter not initialized"}
            
        result = await self._wizard_adapter.goto(x, y, z)
        if result.get("success"):
            self._current_position = {"x": x, "y": y, "z": z}
            await self.broadcast_event("position_updated", self._current_position)
        return result
    
    async def handle_follow_route(self, route_name: str, forward: bool = True) -> Dict[str, Any]:
        """
        Follow a predefined route.
        
        Args:
            route_name: Name of the route to follow
            forward: True for start->end, False for end->start
        """
        if route_name not in self._routes:
            return {"success": False, "error": f"Route '{route_name}' not found"}
        
        route = self._routes[route_name]
        points = route if forward else list(reversed(route))
        
        await self.broadcast_event("route_started", {"route": route_name, "forward": forward})
        
        for i, point in enumerate(points):
            result = await self.handle_move_to(point['x'], point['y'], point.get('z'))
            if not result.get("success"):
                await self.broadcast_event("route_error", {"route": route_name, "point": i})
                return result
            
            # Handle special actions (keypresses)
            if 'action' in point:
                await self.handle_send_key(point['action'], point.get('duration', 0.2))
        
        await self.broadcast_event("route_completed", {"route": route_name})
        return {"success": True, "route": route_name, "points_visited": len(points)}
    
    async def handle_send_key(self, key: str, duration: float = 0.1) -> Dict[str, Any]:
        """
        Send a keypress to the game client.
        
        Args:
            key: Key name (W, A, S, D, X, etc.)
            duration: How long to hold the key
        """
        if not self._wizard_adapter:
            return {"success": False, "error": "Wizard adapter not initialized"}
        
        return await self._wizard_adapter.send_key(key, duration)
    
    async def handle_get_position(self) -> Dict[str, Any]:
        """Get the current character position."""
        if not self._wizard_adapter:
            return {"success": False, "error": "Wizard adapter not initialized"}
        
        position = await self._wizard_adapter.get_position()
        if position.get("success"):
            self._current_position = position.get("data")
        return position
    
    async def handle_list_routes(self) -> Dict[str, Any]:
        """List all available routes."""
        return {
            "success": True,
            "routes": list(self._routes.keys()),
            "count": len(self._routes)
        }
    
    # === Public API ===
    
    def get_info(self) -> Dict[str, Any]:
        """Return plugin metadata."""
        return {
            **super().get_info(),
            "routes_loaded": len(self._routes),
            "current_position": self._current_position,
            "wizard_adapter_ready": self._wizard_adapter is not None,
        }


def register(hub: Any) -> GameAutomationPlugin:
    """
    Factory function for plugin registration.
    Called by the Hub's plugin loader.
    """
    config = hub.config if hasattr(hub, 'config') else AASConfig()
    plugin = GameAutomationPlugin(config, hub)
    return plugin

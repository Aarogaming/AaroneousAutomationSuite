"""
Locomotion Controller - Path Following and Movement Logic

Ported from: artifacts/handoff/maelstrom/AutoWizard101/ProjectMaelstrom/
             Scripts/Library/Automatus-v2-master/func/locomotion.py

This module provides path-following capabilities using coordinate-based
navigation. It interfaces with the Wizard101 client via the IPC bridge.
"""

from typing import Dict, Any, List, Optional
from dataclasses import dataclass
from loguru import logger
import asyncio


@dataclass
class Waypoint:
    """Represents a point on a navigation route."""
    x: float
    y: float
    z: float = 0.0
    action: Optional[str] = None  # Special action at this point (keypress)
    
    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> "Waypoint":
        return cls(
            x=float(data.get('x', 0)),
            y=float(data.get('y', 0)),
            z=float(data.get('z', 0)),
            action=data.get('action')
        )
    
    def to_dict(self) -> Dict[str, Any]:
        return {"x": self.x, "y": self.y, "z": self.z, "action": self.action}


@dataclass 
class Route:
    """Represents a navigation route with multiple waypoints."""
    name: str
    location: str
    waypoints: List[Waypoint]
    
    def __len__(self) -> int:
        return len(self.waypoints)
    
    def __iter__(self):
        return iter(self.waypoints)
    
    def reversed(self) -> "Route":
        """Return the route in reverse order."""
        return Route(
            name=f"{self.name}_reverse",
            location=self.location,
            waypoints=list(reversed(self.waypoints))
        )


class LocomotionController:
    """
    Handles character movement and pathfinding.
    
    Ported from Automatus-v2's locomotion.py with adaptations for
    AAS Hub's async architecture and IPC bridge integration.
    
    Key Features:
    - Coordinate-based navigation (goto)
    - Route following (forward/backward)
    - Keypress injection for special actions
    - Pause/resume support for bot control
    """
    
    # Standard movement speed (units per second)
    WIZARD_SPEED = 580.0
    
    # Keypress action mappings
    # From Automatus: -1 = S/X, 0 = X/S, 1 = W
    ACTION_KEYS = {
        'forward': 'W',
        'backward': 'S', 
        'interact': 'X',
        'mount': 'Z',
        'spell_menu': 'B',
    }
    
    def __init__(self, wizard_speed: float = None, logging_enabled: bool = True):
        self.wizard_speed = wizard_speed or self.WIZARD_SPEED
        self.logging_enabled = logging_enabled
        self._paused = False
        self._current_waypoint_index = 0
        self._active_route: Optional[Route] = None
    
    def log(self, message: str):
        """Conditional logging based on settings."""
        if self.logging_enabled:
            logger.debug(f"[Locomotion] {message}")
    
    async def handle_pause(self):
        """
        Check and handle pause state.
        Blocks execution while paused.
        """
        while self._paused:
            await asyncio.sleep(0.1)
    
    def pause(self):
        """Pause movement operations."""
        self._paused = True
        self.log("Movement paused")
    
    def resume(self):
        """Resume movement operations."""
        self._paused = False
        self.log("Movement resumed")
    
    async def follow_route(
        self, 
        route: Route, 
        client_goto_func, 
        client_send_key_func,
        forward: bool = True
    ) -> Dict[str, Any]:
        """
        Follow a route from start to end (or reversed).
        
        This is the main navigation function, ported from Automatus-v2.
        
        Args:
            route: Route object with waypoints
            client_goto_func: Async function to move client (x, y) -> bool
            client_send_key_func: Async function to send keypresses (key, duration) -> bool
            forward: True for start->end, False for end->start
            
        Returns:
            Dict with success status and visited waypoints
        """
        self.log(f"Beginning route to {route.location}")
        self._active_route = route if forward else route.reversed()
        self._current_waypoint_index = 0
        
        waypoints = list(self._active_route)
        visited = 0
        
        for i, waypoint in enumerate(waypoints):
            await self.handle_pause()
            self._current_waypoint_index = i
            
            # Handle special keypress waypoints (x=0, y=0)
            if waypoint.x == 0 and waypoint.y == 0:
                if waypoint.z == -1:
                    # Interact action
                    await client_send_key_func('X', 0.2)
                    continue
                elif waypoint.z == 0:
                    # Backward movement
                    await client_send_key_func('S', 0.5)
                    continue
                elif waypoint.z == 1:
                    # Forward movement
                    await client_send_key_func('W', 0.5)
                    continue
            
            # Standard coordinate movement
            self.log(f"Moving client to: {waypoint.x}, {waypoint.y}")
            success = await client_goto_func(waypoint.x, waypoint.y)
            
            if not success:
                self.log(f"Failed to reach waypoint {i}")
                return {
                    "success": False,
                    "error": f"Failed at waypoint {i}",
                    "visited": visited,
                    "total": len(waypoints)
                }
            
            # Execute action if defined
            if waypoint.action:
                key = self.ACTION_KEYS.get(waypoint.action, waypoint.action)
                await client_send_key_func(key, 0.3)
            
            visited += 1
        
        self._active_route = None
        self.log(f"Route completed: {visited}/{len(waypoints)} waypoints")
        
        return {
            "success": True,
            "visited": visited,
            "total": len(waypoints),
            "route": route.name
        }
    
    def get_progress(self) -> Dict[str, Any]:
        """Get current navigation progress."""
        if not self._active_route:
            return {"active": False}
        
        return {
            "active": True,
            "route": self._active_route.name,
            "current_waypoint": self._current_waypoint_index,
            "total_waypoints": len(self._active_route),
            "paused": self._paused
        }
    
    @staticmethod
    def parse_route_file(content: str, route_name: str = "custom") -> Route:
        """
        Parse a route file in Automatus format.
        
        Format: Each line is "x,y,z" or special action codes.
        First line is the location name.
        
        Args:
            content: Raw file content
            route_name: Name for the route
            
        Returns:
            Route object with parsed waypoints
        """
        lines = content.strip().split('\n')
        location = lines[0] if lines else route_name
        waypoints = []
        
        for line in lines[1:]:
            line = line.strip()
            if not line or line.startswith('#'):
                continue
            
            parts = line.split(',')
            if len(parts) >= 3:
                waypoints.append(Waypoint(
                    x=float(parts[0]),
                    y=float(parts[1]),
                    z=float(parts[2])
                ))
        
        return Route(name=route_name, location=location, waypoints=waypoints)

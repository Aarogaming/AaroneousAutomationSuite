"""
Universal Game Adapter Interface for AAS

This module provides a standardized interface for controlling different games
and applications. Adapters abstract away game-specific implementation details,
enabling plugins to work across multiple games without modification.

Architecture:
- GameAdapter: Abstract base class defining the adapter interface
- Specific adapters (Wizard101Adapter, Win32Adapter, etc.)
- AdapterRegistry: Factory for discovering and creating adapters
- State caching, async support, and lifecycle hooks
"""

from abc import ABC, abstractmethod
from typing import Any, Dict, Optional, List, Callable, Tuple
from dataclasses import dataclass, field
from enum import Enum
from loguru import logger
import asyncio
import time


class AdapterState(Enum):
    """Adapter lifecycle states"""
    UNINITIALIZED = "uninitialized"
    CONNECTING = "connecting"
    CONNECTED = "connected"
    DISCONNECTED = "disconnected"
    ERROR = "error"


class InputType(Enum):
    """Types of input events"""
    MOUSE_CLICK = "mouse_click"
    MOUSE_MOVE = "mouse_move"
    MOUSE_DRAG = "mouse_drag"
    KEY_PRESS = "key_press"
    KEY_RELEASE = "key_release"
    KEY_COMBO = "key_combo"
    TEXT_INPUT = "text_input"


@dataclass
class GameState:
    """Structured representation of game state"""
    timestamp: float = field(default_factory=time.time)
    window_title: str = ""
    window_handle: Optional[int] = None
    screen_region: Optional[Tuple[int, int, int, int]] = None  # (x, y, width, height)
    player_stats: Dict[str, Any] = field(default_factory=dict)
    entities: List[Dict[str, Any]] = field(default_factory=list)
    ui_elements: List[Dict[str, Any]] = field(default_factory=list)
    raw_data: Dict[str, Any] = field(default_factory=dict)
    
    def __repr__(self):
        return f"GameState(window='{self.window_title}', entities={len(self.entities)}, ui={len(self.ui_elements)})"


@dataclass
class AdapterCapabilities:
    """Describes what an adapter can do"""
    has_window_detection: bool = True
    has_state_reading: bool = True
    has_input_injection: bool = True
    has_screenshot: bool = False
    has_grpc_bridge: bool = False
    has_memory_reading: bool = False
    supports_async: bool = True
    max_actions_per_second: int = 100


class GameAdapter(ABC):
    """
    Abstract base class for game adapters.
    
    Adapters standardize how AAS interacts with different games/applications.
    They handle:
    - Window detection and management
    - Input injection (mouse, keyboard)
    - State reading (game data, UI elements)
    - Lifecycle management (connect, disconnect, health checks)
    
    Subclasses must implement abstract methods and can override lifecycle hooks.
    """
    
    def __init__(self, game_name: str, config: Optional[Dict[str, Any]] = None):
        self.game_name = game_name
        self.config = config or {}
        self.state = AdapterState.UNINITIALIZED
        self._state_cache: Optional[GameState] = None
        self._cache_ttl: float = self.config.get("cache_ttl", 0.1)  # 100ms default
        self._last_cache_time: float = 0
        self._event_handlers: Dict[str, List[Callable]] = {}
        self.capabilities = self._get_capabilities()
        
    @abstractmethod
    def _get_capabilities(self) -> AdapterCapabilities:
        """Return adapter capabilities"""
        pass
    
    @abstractmethod
    async def connect(self) -> bool:
        """
        Establish connection to the game/application.
        
        Returns:
            True if connection successful, False otherwise
        """
        pass
    
    @abstractmethod
    async def disconnect(self) -> bool:
        """
        Clean up and disconnect from the game.
        
        Returns:
            True if disconnection successful, False otherwise
        """
        pass
    
    @abstractmethod
    async def is_connected(self) -> bool:
        """Check if adapter is currently connected"""
        pass
    
    @abstractmethod
    async def find_window(self) -> bool:
        """
        Locate the game window.
        
        Returns:
            True if window found, False otherwise
        """
        pass
    
    @abstractmethod
    async def click(self, x: int, y: int, button: str = "left", duration: float = 0.1) -> bool:
        """
        Simulate mouse click at coordinates.
        
        Args:
            x: X coordinate (relative to game window)
            y: Y coordinate (relative to game window)
            button: Mouse button ("left", "right", "middle")
            duration: Click duration in seconds
            
        Returns:
            True if click successful, False otherwise
        """
        pass
    
    @abstractmethod
    async def move_mouse(self, x: int, y: int, duration: float = 0.5) -> bool:
        """
        Move mouse to coordinates.
        
        Args:
            x: X coordinate
            y: Y coordinate
            duration: Movement duration (for smooth motion)
            
        Returns:
            True if movement successful, False otherwise
        """
        pass
    
    @abstractmethod
    async def send_key(self, key: str, modifiers: Optional[List[str]] = None) -> bool:
        """
        Simulate key press.
        
        Args:
            key: Key to press (e.g., "a", "enter", "f1")
            modifiers: Optional modifier keys (e.g., ["ctrl", "shift"])
            
        Returns:
            True if keypress successful, False otherwise
        """
        pass
    
    @abstractmethod
    async def send_text(self, text: str, delay: float = 0.05) -> bool:
        """
        Type text string.
        
        Args:
            text: Text to type
            delay: Delay between characters
            
        Returns:
            True if text input successful, False otherwise
        """
        pass
    
    @abstractmethod
    async def get_state(self, force_refresh: bool = False) -> GameState:
        """
        Get current game state.
        
        Args:
            force_refresh: If True, bypass cache and fetch fresh state
            
        Returns:
            GameState object with current game information
        """
        pass
    
    # Lifecycle hooks (can be overridden)
    
    async def on_connect(self):
        """Called after successful connection"""
        logger.info(f"{self.game_name} adapter connected")
        await self._emit_event("connected")
    
    async def on_disconnect(self):
        """Called after disconnection"""
        logger.info(f"{self.game_name} adapter disconnected")
        await self._emit_event("disconnected")
    
    async def on_error(self, error: Exception):
        """Called when an error occurs"""
        logger.error(f"{self.game_name} adapter error: {error}")
        self.state = AdapterState.ERROR
        await self._emit_event("error", error=error)
    
    async def health_check(self) -> bool:
        """
        Check if adapter is healthy and responsive.
        
        Returns:
            True if healthy, False otherwise
        """
        try:
            is_conn = await self.is_connected()
            if not is_conn:
                return False
            
            # Try to get state (quick health check)
            state = await self.get_state()
            return state is not None
        except Exception as e:
            logger.warning(f"Health check failed for {self.game_name}: {e}")
            return False
    
    # Event system
    
    def on(self, event: str, handler: Callable):
        """Register event handler"""
        if event not in self._event_handlers:
            self._event_handlers[event] = []
        self._event_handlers[event].append(handler)
    
    async def _emit_event(self, event: str, **kwargs):
        """Emit event to all registered handlers"""
        if event in self._event_handlers:
            for handler in self._event_handlers[event]:
                try:
                    if asyncio.iscoroutinefunction(handler):
                        await handler(**kwargs)
                    else:
                        handler(**kwargs)
                except Exception as e:
                    logger.error(f"Error in event handler for {event}: {e}")
    
    # State caching
    
    async def _get_cached_state(self, force_refresh: bool = False) -> Optional[GameState]:
        """Helper method for implementing state caching in subclasses"""
        now = time.time()
        if force_refresh or not self._state_cache or (now - self._last_cache_time) > self._cache_ttl:
            return None
        return self._state_cache
    
    def _update_cache(self, state: GameState):
        """Update state cache"""
        self._state_cache = state
        self._last_cache_time = time.time()
    
    def __repr__(self):
        return f"{self.__class__.__name__}(game='{self.game_name}', state={self.state.value})"


class Wizard101Adapter(GameAdapter):
    """
    Adapter for Wizard101 using the Maelstrom gRPC bridge.
    
    This adapter communicates with Project Maelstrom (C# game client) via gRPC
    for reliable, high-performance game automation.
    """
    
    def __init__(self, stub: Any = None, config: Optional[Dict[str, Any]] = None):
        super().__init__("Wizard101", config)
        self.stub = stub
        self.window_handle: Optional[int] = None
        self._snapshot_stream: Optional[Any] = None
        
    def _get_capabilities(self) -> AdapterCapabilities:
        return AdapterCapabilities(
            has_window_detection=True,
            has_state_reading=True,
            has_input_injection=True,
            has_screenshot=True,
            has_grpc_bridge=True,
            has_memory_reading=True,
            supports_async=True,
            max_actions_per_second=100
        )
    
    async def connect(self) -> bool:
        """Connect to Maelstrom gRPC server"""
        try:
            self.state = AdapterState.CONNECTING
            logger.info("Connecting to Maelstrom gRPC bridge...")
            
            if self.stub is None:
                # Initialize gRPC stub here (would need actual gRPC setup)
                logger.error("No gRPC stub provided to Wizard101Adapter")
                self.state = AdapterState.ERROR
                return False
            
            # Test connection with a health check command
            found = await self.find_window()
            if not found:
                logger.warning("Could not find Wizard101 window, but adapter connected")
            
            self.state = AdapterState.CONNECTED
            await self.on_connect()
            return True
            
        except Exception as e:
            await self.on_error(e)
            return False
    
    async def disconnect(self) -> bool:
        """Disconnect from Maelstrom"""
        try:
            if self._snapshot_stream:
                # Close snapshot stream
                pass
            
            self.state = AdapterState.DISCONNECTED
            await self.on_disconnect()
            return True
            
        except Exception as e:
            await self.on_error(e)
            return False
    
    async def is_connected(self) -> bool:
        """Check if connected to Maelstrom"""
        return self.state == AdapterState.CONNECTED
    
    async def find_window(self) -> bool:
        """Find Wizard101 game window"""
        try:
            logger.info("Searching for Wizard101 game window...")
            
            # Would call Maelstrom gRPC command here
            # Example: response = await self.stub.FindWindow(FindWindowRequest())
            # self.window_handle = response.window_handle
            
            # For now, simulate success
            self.window_handle = 12345  # Placeholder
            logger.success(f"Found Wizard101 window: {self.window_handle}")
            return True
            
        except Exception as e:
            logger.error(f"Failed to find Wizard101 window: {e}")
            return False
    
    async def click(self, x: int, y: int, button: str = "left", duration: float = 0.1) -> bool:
        """Click at coordinates via Maelstrom"""
        try:
            logger.debug(f"Wizard101: Clicking at ({x}, {y}) with {button} button")
            
            # Would call Maelstrom gRPC command here
            # Example: await self.stub.ExecuteCommand(ClickCommand(x=x, y=y, button=button))
            
            await self._emit_event("click", x=x, y=y, button=button)
            return True
            
        except Exception as e:
            logger.error(f"Click failed: {e}")
            return False
    
    async def move_mouse(self, x: int, y: int, duration: float = 0.5) -> bool:
        """Move mouse to coordinates"""
        try:
            logger.debug(f"Wizard101: Moving mouse to ({x}, {y})")
            
            # Would call Maelstrom gRPC command here
            
            await self._emit_event("mouse_move", x=x, y=y)
            return True
            
        except Exception as e:
            logger.error(f"Mouse move failed: {e}")
            return False
    
    async def send_key(self, key: str, modifiers: Optional[List[str]] = None) -> bool:
        """Send key press via Maelstrom"""
        try:
            modifiers = modifiers or []
            logger.debug(f"Wizard101: Sending key '{key}' with modifiers {modifiers}")
            
            if self.stub:
                import json
                from core.ipc.protos import bridge_pb2
                payload = json.dumps({"key": key, "modifiers": modifiers})
                await self.stub.ExecuteCommand(bridge_pb2.CommandRequest(
                    command_type="KEY_PRESS",
                    payload=payload
                ))
            
            await self._emit_event("key_press", key=key, modifiers=modifiers)
            return True
            
        except Exception as e:
            logger.error(f"Key press failed: {e}")
            return False
    
    async def send_text(self, text: str, delay: float = 0.05) -> bool:
        """Type text string"""
        try:
            logger.debug(f"Wizard101: Typing text: '{text[:20]}...'")
            
            for char in text:
                await self.send_key(char)
                await asyncio.sleep(delay)
            
            return True
            
        except Exception as e:
            logger.error(f"Text input failed: {e}")
            return False
    
    async def get_state(self, force_refresh: bool = False) -> GameState:
        """Get current Wizard101 game state via Maelstrom"""
        # Check cache first
        cached = await self._get_cached_state(force_refresh)
        if cached:
            return cached
        
        try:
            logger.debug("Fetching Wizard101 game state from Maelstrom...")
            
            # Would call Maelstrom gRPC StreamSnapshots here
            # Example: snapshot = await self.stub.GetSnapshot()
            
            # For now, create mock state
            state = GameState(
                window_title="Wizard101",
                window_handle=self.window_handle,
                player_stats={
                    "health": 100,
                    "mana": 50,
                    "gold": 1000,
                    "level": 42
                },
                entities=[],
                ui_elements=[],
                raw_data={}
            )
            
            self._update_cache(state)
            return state
            
        except Exception as e:
            logger.error(f"Failed to get game state: {e}")
            # Return empty state on error
            return GameState()


class Win32Adapter(GameAdapter):
    """
    Generic Windows adapter using Win32 API.
    
    Fallback adapter for games without specialized integration.
    Uses pywin32 or pyautogui for basic window and input control.
    """
    
    def __init__(self, game_name: str, window_title_pattern: str, config: Optional[Dict[str, Any]] = None):
        super().__init__(game_name, config)
        self.window_title_pattern = window_title_pattern
        self.window_handle: Optional[int] = None
        
    def _get_capabilities(self) -> AdapterCapabilities:
        return AdapterCapabilities(
            has_window_detection=True,
            has_state_reading=False,  # Limited to window info only
            has_input_injection=True,
            has_screenshot=True,
            has_grpc_bridge=False,
            has_memory_reading=False,
            supports_async=True,
            max_actions_per_second=50
        )
    
    async def connect(self) -> bool:
        """Connect to Windows application"""
        try:
            self.state = AdapterState.CONNECTING
            logger.info(f"Connecting to {self.game_name} via Win32 API...")
            
            found = await self.find_window()
            if not found:
                logger.error(f"Could not find window matching '{self.window_title_pattern}'")
                self.state = AdapterState.ERROR
                return False
            
            self.state = AdapterState.CONNECTED
            await self.on_connect()
            return True
            
        except Exception as e:
            await self.on_error(e)
            return False
    
    async def disconnect(self) -> bool:
        """Disconnect from application"""
        self.state = AdapterState.DISCONNECTED
        await self.on_disconnect()
        return True
    
    async def is_connected(self) -> bool:
        """Check if connected"""
        return self.state == AdapterState.CONNECTED and self.window_handle is not None
    
    async def find_window(self) -> bool:
        """Find window by title pattern using Win32 API"""
        try:
            logger.info(f"Searching for window matching '{self.window_title_pattern}'...")
            
            # Would use pywin32 win32gui.FindWindow or similar here
            # For now, simulate
            self.window_handle = 67890  # Placeholder
            logger.success(f"Found window: {self.window_handle}")
            return True
            
        except Exception as e:
            logger.error(f"Failed to find window: {e}")
            return False
    
    async def click(self, x: int, y: int, button: str = "left", duration: float = 0.1) -> bool:
        """Click using Win32 PostMessage or pyautogui"""
        try:
            logger.debug(f"{self.game_name}: Clicking at ({x}, {y})")
            
            # Would use win32api.PostMessage or pyautogui.click here
            
            await self._emit_event("click", x=x, y=y, button=button)
            return True
            
        except Exception as e:
            logger.error(f"Click failed: {e}")
            return False
    
    async def move_mouse(self, x: int, y: int, duration: float = 0.5) -> bool:
        """Move mouse using pyautogui"""
        try:
            logger.debug(f"{self.game_name}: Moving mouse to ({x}, {y})")
            
            # Would use pyautogui.moveTo here
            
            return True
            
        except Exception as e:
            logger.error(f"Mouse move failed: {e}")
            return False
    
    async def send_key(self, key: str, modifiers: Optional[List[str]] = None) -> bool:
        """Send key using Win32 SendMessage or pyautogui"""
        try:
            modifiers = modifiers or []
            logger.debug(f"{self.game_name}: Sending key '{key}' with modifiers {modifiers}")
            
            # Would use win32api.SendMessage or pyautogui.press here
            
            return True
            
        except Exception as e:
            logger.error(f"Key press failed: {e}")
            return False
    
    async def send_text(self, text: str, delay: float = 0.05) -> bool:
        """Type text using pyautogui"""
        try:
            logger.debug(f"{self.game_name}: Typing text: '{text[:20]}...'")
            
            # Would use pyautogui.write here
            
            return True
            
        except Exception as e:
            logger.error(f"Text input failed: {e}")
            return False
    
    async def get_state(self, force_refresh: bool = False) -> GameState:
        """Get basic window state (Win32Adapter has limited state reading)"""
        cached = await self._get_cached_state(force_refresh)
        if cached:
            return cached
        
        try:
            # Can only get window information, not game-specific state
            state = GameState(
                window_title=self.window_title_pattern,
                window_handle=self.window_handle,
                raw_data={"adapter_type": "Win32", "limited_state": True}
            )
            
            self._update_cache(state)
            return state
            
        except Exception as e:
            logger.error(f"Failed to get state: {e}")
            return GameState()


class AdapterRegistry:
    """
    Factory for discovering and creating game adapters.
    
    Maintains registry of available adapters and provides auto-detection.
    """
    
    def __init__(self):
        self._adapters: Dict[str, type] = {}
        self._instances: Dict[str, GameAdapter] = {}
        
        # Register built-in adapters
        self.register("wizard101", Wizard101Adapter)
        self.register("win32", Win32Adapter)
    
    def register(self, game_id: str, adapter_class: type):
        """Register an adapter class"""
        if not issubclass(adapter_class, GameAdapter):
            raise ValueError(f"{adapter_class} must inherit from GameAdapter")
        
        self._adapters[game_id.lower()] = adapter_class
        logger.info(f"Registered adapter: {game_id} -> {adapter_class.__name__}")
    
    def get_adapter(self, game_id: str, **kwargs) -> Optional[GameAdapter]:
        """
        Get or create adapter instance for a game.
        
        Args:
            game_id: Game identifier (e.g., "wizard101")
            **kwargs: Arguments to pass to adapter constructor
            
        Returns:
            GameAdapter instance or None if not found
        """
        game_id = game_id.lower()
        
        # Return existing instance if available
        if game_id in self._instances:
            return self._instances[game_id]
        
        # Create new instance
        if game_id not in self._adapters:
            logger.error(f"No adapter registered for '{game_id}'")
            return None
        
        adapter_class = self._adapters[game_id]
        adapter = adapter_class(**kwargs)
        self._instances[game_id] = adapter
        
        logger.info(f"Created adapter instance: {game_id} -> {adapter}")
        return adapter
    
    def list_adapters(self) -> List[str]:
        """List all registered adapter IDs"""
        return list(self._adapters.keys())
    
    async def auto_detect(self) -> Optional[GameAdapter]:
        """
        Auto-detect running games and return appropriate adapter.
        
        Returns:
            GameAdapter for detected game, or None if no game found
        """
        logger.info("Auto-detecting running games...")
        
        # Try Wizard101 first
        w101_adapter = self.get_adapter("wizard101")
        if w101_adapter:
            if await w101_adapter.find_window():
                logger.success("Detected Wizard101")
                return w101_adapter
        
        # Could add more detection logic here
        
        logger.warning("No supported games detected")
        return None


# Global registry instance
adapter_registry = AdapterRegistry()


# Convenience functions
async def get_adapter_for_game(game_id: str, **kwargs) -> Optional[GameAdapter]:
    """Get adapter for specified game"""
    return adapter_registry.get_adapter(game_id, **kwargs)


async def detect_game() -> Optional[GameAdapter]:
    """Auto-detect running game and return adapter"""
    return await adapter_registry.auto_detect()

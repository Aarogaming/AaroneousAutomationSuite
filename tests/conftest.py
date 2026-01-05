import pytest
import asyncio
from typing import Any, Dict, Optional
from core.managers import ManagerHub
from core.managers.adapters.base import GameAdapter, AdapterCapabilities, GameState, AdapterState

class MockAdapter(GameAdapter):
    """
    Mock adapter for headless testing.
    Simulates game state and input injection.
    """
    def __init__(self, game_name: str = "MockGame", config: Optional[Dict[str, Any]] = None):
        super().__init__(game_name, config)
        self.connected = False
        self.window_found = True
        self.mock_state = GameState(window_title=game_name)

    def _get_capabilities(self) -> AdapterCapabilities:
        return AdapterCapabilities(
            has_window_detection=True,
            has_state_reading=True,
            has_input_injection=True
        )

    async def connect(self) -> bool:
        self.connected = True
        self.state = AdapterState.CONNECTED
        return True

    async def disconnect(self) -> bool:
        self.connected = False
        self.state = AdapterState.DISCONNECTED
        return True

    async def is_connected(self) -> bool:
        return self.connected

    async def find_window(self) -> bool:
        return self.window_found

    async def click(self, x: int, y: int, button: str = "left", duration: float = 0.1) -> bool:
        return True

    async def move_mouse(self, x: int, y: int, duration: float = 0.5) -> bool:
        return True

    async def send_key(self, key: str, modifiers: Optional[list[str]] = None) -> bool:
        return True

    async def send_text(self, text: str, delay: float = 0.05) -> bool:
        return True

    async def get_state(self, force_refresh: bool = False) -> GameState:
        return self.mock_state

@pytest.fixture
def mock_hub():
    """Fixture for a ManagerHub with mock components."""
    hub = ManagerHub.create()
    return hub

@pytest.fixture
def mock_adapter():
    """Fixture for a MockAdapter."""
    return MockAdapter()

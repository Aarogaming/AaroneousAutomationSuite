# Universal Game Adapter Interface

## Overview

The Universal Game Adapter Interface (AAS-018) provides a standardized way to interact with different games and applications. It abstracts game-specific implementation details, enabling automation plugins to work across multiple games without modification.

## Architecture

### Core Components

1. **GameAdapter** (Abstract Base Class)
   - Defines the standard interface all adapters must implement
   - Provides lifecycle management (connect, disconnect, health checks)
   - Includes event system for notifications
   - Implements state caching for performance

2. **Specific Adapters**
   - **Wizard101Adapter**: Uses Maelstrom gRPC bridge for robust game control
   - **Win32Adapter**: Fallback adapter using Win32 API for generic window control
   - Custom adapters can be created for other games

3. **AdapterRegistry**
   - Factory pattern for discovering and creating adapters
   - Singleton management (one adapter instance per game)
   - Auto-detection of running games

4. **Supporting Types**
   - **GameState**: Structured representation of game state
   - **AdapterCapabilities**: Describes what an adapter can do
   - **AdapterState**: Tracks adapter lifecycle state

## Quick Start

### Using an Adapter

```python
import asyncio
from core.handoff.adapter import get_adapter_for_game

async def main():
    # Get adapter for Wizard101
    adapter = await get_adapter_for_game("wizard101", stub=grpc_stub)
    
    # Connect to the game
    if await adapter.connect():
        print("Connected!")
        
        # Find game window
        await adapter.find_window()
        
        # Perform actions
        await adapter.click(100, 200)
        await adapter.send_key("w")
        await adapter.send_text("Hello World")
        
        # Get game state
        state = await adapter.get_state()
        print(f"Player stats: {state.player_stats}")
        
        # Cleanup
        await adapter.disconnect()

asyncio.run(main())
```

### Auto-Detection

```python
from core.handoff.adapter import detect_game

async def auto_connect():
    # Automatically detect running game
    adapter = await detect_game()
    
    if adapter:
        print(f"Detected: {adapter.game_name}")
        # Use adapter...
    else:
        print("No supported games found")
```

### Creating a Custom Adapter

```python
from core.handoff.adapter import GameAdapter, AdapterCapabilities, GameState

class MyGameAdapter(GameAdapter):
    def __init__(self, config=None):
        super().__init__("MyGame", config)
        
    def _get_capabilities(self) -> AdapterCapabilities:
        return AdapterCapabilities(
            has_window_detection=True,
            has_state_reading=True,
            has_input_injection=True
        )
    
    async def connect(self) -> bool:
        self.state = AdapterState.CONNECTING
        # ... connection logic ...
        self.state = AdapterState.CONNECTED
        await self.on_connect()
        return True
    
    # Implement other abstract methods...
    
# Register the adapter
from core.handoff.adapter import adapter_registry
adapter_registry.register("mygame", MyGameAdapter)
```

## API Reference

### GameAdapter Methods

#### Lifecycle

- **`async connect() -> bool`**: Establish connection to the game
- **`async disconnect() -> bool`**: Clean up and disconnect
- **`async is_connected() -> bool`**: Check if currently connected
- **`async health_check() -> bool`**: Verify adapter is healthy

#### Input Injection

- **`async click(x, y, button="left", duration=0.1) -> bool`**: Simulate mouse click
- **`async move_mouse(x, y, duration=0.5) -> bool`**: Move mouse cursor
- **`async send_key(key, modifiers=None) -> bool`**: Send key press
- **`async send_text(text, delay=0.05) -> bool`**: Type text string

#### State Reading

- **`async get_state(force_refresh=False) -> GameState`**: Get current game state
- **`async find_window() -> bool`**: Locate game window

#### Events

- **`on(event, handler)`**: Register event handler
- Events: `connected`, `disconnected`, `error`, `click`, `key_press`, `mouse_move`

### GameState Structure

```python
@dataclass
class GameState:
    timestamp: float  # When state was captured
    window_title: str  # Window title
    window_handle: Optional[int]  # OS window handle
    screen_region: Optional[Tuple]  # (x, y, width, height)
    player_stats: Dict[str, Any]  # Player stats (health, mana, etc.)
    entities: List[Dict]  # Nearby entities/NPCs
    ui_elements: List[Dict]  # UI element positions
    raw_data: Dict[str, Any]  # Adapter-specific data
```

### AdapterCapabilities

```python
@dataclass
class AdapterCapabilities:
    has_window_detection: bool  # Can find game window
    has_state_reading: bool  # Can read game state
    has_input_injection: bool  # Can send input
    has_screenshot: bool  # Can capture screenshots
    has_grpc_bridge: bool  # Uses gRPC for communication
    has_memory_reading: bool  # Can read game memory
    supports_async: bool  # Supports async operations
    max_actions_per_second: int  # Rate limit
```

## Adapter Comparison

| Feature | Wizard101Adapter | Win32Adapter |
|---------|-----------------|--------------|
| Window Detection | ✅ | ✅ |
| State Reading | ✅ (Rich) | ⚠️  (Limited) |
| Input Injection | ✅ | ✅ |
| Screenshot | ✅ | ✅ |
| gRPC Bridge | ✅ | ❌ |
| Memory Reading | ✅ | ❌ |
| Max Actions/sec | 100 | 50 |

## Event System

Adapters emit events for important actions:

```python
adapter = await get_adapter_for_game("wizard101")

# Register handlers
adapter.on("connected", lambda: print("Connected!"))
adapter.on("error", lambda error: print(f"Error: {error}"))
adapter.on("click", lambda x, y, button: print(f"Clicked at ({x}, {y})"))

await adapter.connect()
await adapter.click(100, 200)
```

## State Caching

Adapters automatically cache game state to reduce overhead:

```python
# First call fetches fresh state
state1 = await adapter.get_state()  # Fresh fetch

# Subsequent calls within cache TTL use cached state
state2 = await adapter.get_state()  # From cache (fast!)

# Force refresh bypass cache
state3 = await adapter.get_state(force_refresh=True)  # Fresh fetch
```

Cache TTL can be configured:

```python
adapter = Wizard101Adapter(config={"cache_ttl": 0.2})  # 200ms cache
```

## Best Practices

### Error Handling

```python
try:
    await adapter.click(x, y)
except Exception as e:
    logger.error(f"Click failed: {e}")
    # Handle error...
```

### Health Monitoring

```python
# Periodic health checks
while True:
    if not await adapter.health_check():
        logger.warning("Adapter unhealthy, reconnecting...")
        await adapter.disconnect()
        await adapter.connect()
    
    await asyncio.sleep(30)
```

### Resource Cleanup

```python
async with adapter:  # (if context manager implemented)
    await adapter.click(100, 200)
    # Automatically disconnects on exit

# Or manually:
try:
    await adapter.connect()
    # ... use adapter ...
finally:
    await adapter.disconnect()
```

### Rate Limiting

```python
# Respect adapter's max action rate
caps = adapter.capabilities
max_rate = caps.max_actions_per_second
delay = 1.0 / max_rate

for action in actions:
    await adapter.send_key(action)
    await asyncio.sleep(delay)
```

## Testing

Run the adapter test suite:

```bash
python scripts/test_adapters.py
```

Tests cover:
- Adapter lifecycle (connect/disconnect/health)
- Input injection (mouse, keyboard)
- State reading and caching
- Event system
- Registry and factory pattern
- Capability reporting

## Integration with AAS

### Using in Plugins

```python
# In your plugin
from core.handoff.adapter import get_adapter_for_game

class MyPlugin:
    async def initialize(self, hub):
        self.adapter = await get_adapter_for_game("wizard101")
        await self.adapter.connect()
    
    async def farm_gold(self):
        # Use adapter for automation
        await self.adapter.click(portal_x, portal_y)
        await asyncio.sleep(2)
        state = await self.adapter.get_state()
        # ... automation logic ...
```

### IPC Integration

Wizard101Adapter integrates with Maelstrom gRPC bridge:

```python
# core/ipc/server.py provides gRPC stub
from core.ipc_server import get_maelstrom_stub

stub = await get_maelstrom_stub()
adapter = Wizard101Adapter(stub=stub)
await adapter.connect()
```

## Future Enhancements

Planned improvements (see task board):

- **AAS-052**: Computer vision for UI element detection
- **AAS-059**: Reinforcement learning for optimal actions
- **AAS-091**: Character build optimizer using adapter
- **AAS-095**: Auction house trading bot using adapter
- **AAS-096**: Multi-character team coordination

## Troubleshooting

### Adapter Won't Connect

1. Check if game is running
2. Verify window title pattern (for Win32Adapter)
3. Check gRPC connection (for Wizard101Adapter)
4. Review logs for error messages

### Actions Not Working

1. Verify adapter has input_injection capability
2. Check if game window has focus
3. Ensure coordinates are within window bounds
4. Reduce action rate if hitting limits

### State Reading Fails

1. Verify adapter has state_reading capability
2. Check if gRPC bridge is running (Wizard101)
3. Clear state cache with `force_refresh=True`
4. Review adapter-specific requirements

## Related Documentation

- [Maelstrom gRPC Bridge](../game_manager/maelstrom/README.md)
- [Plugin Development](../docs/PLUGIN_DEV.md)
- [IPC Server](../core/ipc/README.md)
- [Quest Framework](../docs/QUESTS.md)

## Contributing

To add support for a new game:

1. Create adapter class inheriting from `GameAdapter`
2. Implement all abstract methods
3. Define capabilities
4. Add tests in `scripts/test_adapters.py`
5. Register adapter in `AdapterRegistry`
6. Update this documentation

See [CONTRIBUTING.md](../CONTRIBUTING.md) for guidelines.

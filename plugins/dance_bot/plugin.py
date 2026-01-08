"""
DanceBot Plugin - Wizard101 Pet Dance Minigame Automation

!!! DEPRECATED !!!
This standalone plugin has been deprecated in favor of the unified 
minigame trainer system in game_automation plugin.

Use instead:
    IPC: game.trainer.start name=dance difficulty=easy
    Or via game_automation.minigames.DanceGameTrainer

Migration complete as of v0.2.0. This plugin will be removed in a future release.

Task Reference: AAS-014 (DanceBot Integration)
Dependencies: AAS-012 (AutoWizard101 Migration), AAS-013 (Deimos-Wizard101 Port)

Original Source: https://github.com/kennyhngo/Wizard101_DanceBot
"""

import warnings
from typing import Dict, Any, Optional, List
from loguru import logger
import asyncio

from core.plugin_base import PluginBase
from core.config import AASConfig

# Emit deprecation warning on import
warnings.warn(
    "dance_bot plugin is deprecated. Use game_automation.minigames.DanceGameTrainer instead.",
    DeprecationWarning,
    stacklevel=2
)


class DanceBotPlugin(PluginBase):
    """
    DEPRECATED: Use game_automation plugin's minigame trainers instead.
    
    Automates the Wizard101 Pet Dance minigame.
    
    The pet dance game requires players to press arrow keys in sequence
    as indicators reach the target zone. This bot uses image recognition
    via Maelstrom to detect indicators and time keypresses.
    
    Workflow:
    1. Detect game start via screen capture
    2. Monitor for arrow indicators
    3. Calculate timing based on indicator position
    4. Send keypresses at optimal moment
    """
    
    version = "0.1.0-deprecated"
    
    # Arrow key mappings for dance game
    ARROW_KEYS = {
        'up': 'UP',
        'down': 'DOWN', 
        'left': 'LEFT',
        'right': 'RIGHT'
    }
    
    # Timing constants (milliseconds)
    REACTION_OFFSET = 50  # Pre-emptive offset for network latency
    
    def __init__(self, config: AASConfig, hub: Any):
        super().__init__("dance_bot", config, hub)
        logger.warning("dance_bot plugin is deprecated. Use game_automation minigame trainers.")
        self._game_automation = None
        self._running = False
        self._score = 0
        self._difficulty = getattr(config, 'difficulty', 'easy')
        self._auto_retry = getattr(config, 'auto_retry', True)
        
    async def setup(self) -> bool:
        """Initialize DanceBot and connect to game_automation plugin."""
        try:
            logger.info("Initializing DanceBot Plugin...")
            
            # Get reference to game_automation plugin
            if hasattr(self.hub, 'plugins') and 'game_automation' in self.hub.plugins:
                self._game_automation = self.hub.plugins['game_automation']
            else:
                logger.warning("game_automation plugin not found - DanceBot will have limited functionality")
            
            # Register IPC handlers
            await self._register_ipc_handlers()
            
            logger.success("DanceBot Plugin initialized successfully")
            return True
            
        except Exception as e:
            logger.error(f"Failed to initialize DanceBot: {e}")
            return False
    
    async def shutdown(self) -> bool:
        """Stop any active dance sessions and cleanup."""
        try:
            self._running = False
            logger.info("DanceBot Plugin shut down")
            return True
        except Exception as e:
            logger.error(f"Error during shutdown: {e}")
            return False
    
    async def _register_ipc_handlers(self):
        """Register command handlers with the IPC bridge."""
        if hasattr(self.hub, 'ipc_bridge'):
            handlers = {
                'dance.start': self.handle_start,
                'dance.stop': self.handle_stop,
                'dance.calibrate': self.handle_calibrate,
                'dance.status': self.handle_status,
            }
            for cmd, handler in handlers.items():
                self.hub.ipc_bridge.register_handler(cmd, handler)
                logger.debug(f"Registered IPC handler: {cmd}")
    
    # === IPC Command Handlers ===
    
    async def handle_start(self, difficulty: Optional[str] = None) -> Dict[str, Any]:
        """
        Start the dance bot automation.
        
        Args:
            difficulty: Optional difficulty override (easy/medium/hard)
        """
        if self._running:
            return {"success": False, "error": "Dance bot already running"}
        
        self._difficulty = difficulty or self._difficulty
        self._running = True
        self._score = 0
        
        await self.broadcast_event("dance_started", {"difficulty": self._difficulty})
        
        # Start the main automation loop
        asyncio.create_task(self._dance_loop())
        
        return {"success": True, "difficulty": self._difficulty}
    
    async def handle_stop(self) -> Dict[str, Any]:
        """Stop the dance bot automation."""
        if not self._running:
            return {"success": False, "error": "Dance bot not running"}
        
        self._running = False
        
        await self.broadcast_event("dance_stopped", {"final_score": self._score})
        
        return {"success": True, "final_score": self._score}
    
    async def handle_calibrate(self) -> Dict[str, Any]:
        """
        Calibrate timing offsets for the current game.
        
        This adjusts the reaction timing based on current latency
        and game speed settings.
        """
        # TODO: Implement calibration via Maelstrom's image recognition
        logger.info("Calibrating dance bot timing...")
        
        return {
            "success": True,
            "reaction_offset": self.REACTION_OFFSET,
            "message": "Calibration placeholder - requires Maelstrom integration"
        }
    
    async def handle_status(self) -> Dict[str, Any]:
        """Get current dance bot status."""
        return {
            "running": self._running,
            "score": self._score,
            "difficulty": self._difficulty,
            "auto_retry": self._auto_retry
        }
    
    # === Core Automation Logic ===
    
    async def _dance_loop(self):
        """
        Main automation loop for the dance game.
        
        This loop:
        1. Queries Maelstrom for current game state (via screenshot/OCR)
        2. Detects arrow indicators
        3. Calculates timing
        4. Sends keypresses
        """
        logger.info("Dance loop started")
        
        try:
            while self._running:
                # Request game state from Maelstrom
                # This would use image recognition to detect arrows
                game_state = await self._get_dance_state()
                
                if game_state.get("game_over"):
                    logger.info("Dance game ended")
                    if self._auto_retry and game_state.get("can_retry"):
                        await self._start_new_game()
                    else:
                        self._running = False
                    continue
                
                # Process any detected arrows
                arrows = game_state.get("arrows", [])
                for arrow in arrows:
                    if arrow.get("ready_to_press"):
                        await self._press_arrow(arrow["direction"])
                        self._score += 1
                
                # Small delay to prevent CPU spinning
                await asyncio.sleep(0.016)  # ~60 FPS polling
                
        except Exception as e:
            logger.error(f"Dance loop error: {e}")
            self._running = False
        
        logger.info(f"Dance loop ended - Final score: {self._score}")
    
    async def _get_dance_state(self) -> Dict[str, Any]:
        """
        Get current dance game state from Maelstrom.
        
        This queries Maelstrom's image recognition to detect:
        - Arrow positions and directions
        - Current score
        - Game over state
        """
        if not self._game_automation:
            # Mock state for testing
            return {"arrows": [], "game_over": False, "can_retry": True}
        
        # TODO: Implement actual Maelstrom query
        # This would send a gRPC request to get screenshot analysis
        return {"arrows": [], "game_over": False, "can_retry": True}
    
    async def _press_arrow(self, direction: str):
        """Send an arrow keypress via game_automation."""
        key = self.ARROW_KEYS.get(direction.lower(), direction.upper())
        
        if self._game_automation and hasattr(self._game_automation, '_wizard_adapter'):
            await self._game_automation._wizard_adapter.send_key(key, 0.05)
            logger.debug(f"Pressed arrow: {direction}")
        else:
            logger.debug(f"[MOCK] Would press arrow: {direction}")
    
    async def _start_new_game(self):
        """Start a new dance game (retry after completion)."""
        logger.info("Starting new dance game...")
        
        # Press interact to start new game
        if self._game_automation and hasattr(self._game_automation, '_wizard_adapter'):
            await self._game_automation._wizard_adapter.interact()
        
        self._score = 0
        await asyncio.sleep(1.0)  # Wait for game to initialize
    
    def get_info(self) -> Dict[str, Any]:
        """Return plugin metadata."""
        return {
            **super().get_info(),
            "running": self._running,
            "score": self._score,
            "difficulty": self._difficulty,
            "game_automation_connected": self._game_automation is not None,
        }


def register(hub: Any) -> DanceBotPlugin:
    """Factory function for plugin registration."""
    config = hub.config if hasattr(hub, 'config') else AASConfig()
    plugin = DanceBotPlugin(config, hub)
    return plugin

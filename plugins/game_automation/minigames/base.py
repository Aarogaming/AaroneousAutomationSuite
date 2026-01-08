"""
Minigame Trainer Base Classes

Provides the abstract base for all Wizard101 minigame trainers.
Each trainer is a configurable preset that can be activated via
the game_automation plugin.
"""

from abc import ABC, abstractmethod
from typing import Dict, Any, Optional, List
from dataclasses import dataclass, field
from enum import Enum
from loguru import logger
import asyncio


class TrainerState(Enum):
    """Current state of a trainer."""
    IDLE = "idle"
    CALIBRATING = "calibrating"
    RUNNING = "running"
    PAUSED = "paused"
    ERROR = "error"


@dataclass
class MinigameConfig:
    """
    Base configuration for minigame trainers.
    
    Each minigame can extend this with game-specific settings.
    """
    enabled: bool = True
    difficulty: str = "easy"  # easy, medium, hard
    auto_retry: bool = True
    max_retries: int = 5
    reaction_offset_ms: int = 50  # Timing adjustment for latency
    logging_enabled: bool = True
    
    # Timing profiles per difficulty
    timing_profiles: Dict[str, Dict[str, int]] = field(default_factory=lambda: {
        "easy": {"window_ms": 500, "speed_multiplier": 1.0},
        "medium": {"window_ms": 350, "speed_multiplier": 1.5},
        "hard": {"window_ms": 200, "speed_multiplier": 2.0},
    })
    
    def get_timing(self) -> Dict[str, Any]:
        """Get timing profile for current difficulty."""
        return self.timing_profiles.get(self.difficulty, self.timing_profiles["easy"])


class MinigameTrainer(ABC):
    """
    Abstract base class for Wizard101 minigame trainers.
    
    Trainers are game-specific automation presets that can be:
    - Started/stopped via IPC commands
    - Configured with difficulty and timing settings
    - Calibrated for current game conditions
    - Monitored for performance metrics
    
    Usage:
        trainer = DanceGameTrainer(config, wizard_adapter)
        await trainer.start()
        # ... trainer runs autonomously ...
        await trainer.stop()
    """
    
    # Override in subclass
    TRAINER_NAME: str = "base"
    TRAINER_VERSION: str = "1.0.0"
    
    def __init__(self, config: MinigameConfig, wizard_adapter: Any):
        self.config = config
        self.adapter = wizard_adapter
        self._state = TrainerState.IDLE
        self._score = 0
        self._attempts = 0
        self._successes = 0
        self._task: Optional[asyncio.Task] = None
        
    @property
    def state(self) -> TrainerState:
        return self._state
    
    @property
    def is_running(self) -> bool:
        return self._state == TrainerState.RUNNING
    
    def log(self, message: str, level: str = "debug"):
        """Conditional logging based on config."""
        if self.config.logging_enabled:
            getattr(logger, level)(f"[{self.TRAINER_NAME}] {message}")
    
    # === Lifecycle Methods ===
    
    async def start(self, **kwargs) -> Dict[str, Any]:
        """
        Start the trainer.
        
        Args:
            **kwargs: Trainer-specific start parameters
            
        Returns:
            Status dict with success flag
        """
        if self._state == TrainerState.RUNNING:
            return {"success": False, "error": "Trainer already running"}
        
        self._state = TrainerState.RUNNING
        self._score = 0
        self.log(f"Starting trainer (difficulty={self.config.difficulty})", "info")
        
        # Start the main loop as a background task
        self._task = asyncio.create_task(self._main_loop())
        
        return {"success": True, "trainer": self.TRAINER_NAME}
    
    async def stop(self) -> Dict[str, Any]:
        """Stop the trainer and return final stats."""
        if self._state != TrainerState.RUNNING:
            return {"success": False, "error": "Trainer not running"}
        
        self._state = TrainerState.IDLE
        
        if self._task:
            self._task.cancel()
            try:
                await self._task
            except asyncio.CancelledError:
                pass
            self._task = None
        
        self.log(f"Stopped - Score: {self._score}", "info")
        
        return {
            "success": True,
            "final_score": self._score,
            "attempts": self._attempts,
            "success_rate": self._successes / max(1, self._attempts)
        }
    
    async def pause(self):
        """Pause the trainer."""
        if self._state == TrainerState.RUNNING:
            self._state = TrainerState.PAUSED
            self.log("Paused")
    
    async def resume(self):
        """Resume a paused trainer."""
        if self._state == TrainerState.PAUSED:
            self._state = TrainerState.RUNNING
            self.log("Resumed")
    
    async def calibrate(self) -> Dict[str, Any]:
        """
        Calibrate timing for current game conditions.
        
        Override in subclass for game-specific calibration.
        """
        self._state = TrainerState.CALIBRATING
        self.log("Calibrating...", "info")
        
        # Base calibration just verifies adapter connection
        await asyncio.sleep(0.5)
        
        self._state = TrainerState.IDLE
        return {
            "success": True,
            "reaction_offset": self.config.reaction_offset_ms,
            "timing": self.config.get_timing()
        }
    
    # === Abstract Methods (implement in subclass) ===
    
    @abstractmethod
    async def _main_loop(self):
        """
        Main automation loop. Implement game-specific logic here.
        
        Should:
        1. Check game state via adapter
        2. Detect relevant game events
        3. Execute appropriate actions
        4. Update score/metrics
        5. Handle game-over conditions
        """
        pass
    
    @abstractmethod
    async def _detect_game_state(self) -> Dict[str, Any]:
        """
        Detect current game state.
        
        Returns dict with game-specific state info.
        """
        pass
    
    @abstractmethod
    async def _execute_action(self, action: str, **kwargs) -> bool:
        """
        Execute a game action.
        
        Args:
            action: Action identifier
            **kwargs: Action-specific parameters
            
        Returns:
            True if action succeeded
        """
        pass
    
    # === Status & Metrics ===
    
    def get_status(self) -> Dict[str, Any]:
        """Get current trainer status."""
        return {
            "trainer": self.TRAINER_NAME,
            "version": self.TRAINER_VERSION,
            "state": self._state.value,
            "score": self._score,
            "attempts": self._attempts,
            "successes": self._successes,
            "success_rate": self._successes / max(1, self._attempts),
            "config": {
                "difficulty": self.config.difficulty,
                "auto_retry": self.config.auto_retry,
                "reaction_offset_ms": self.config.reaction_offset_ms,
            }
        }

"""
Dance Game Trainer - Pet Dance Minigame Automation

A trainer preset for the Wizard101 Pet Dance minigame.
Players must press arrow keys as indicators reach the target zone.

This trainer:
- Monitors for arrow indicators via Maelstrom's image recognition
- Calculates optimal keypress timing based on indicator velocity
- Sends keypresses at the right moment for maximum score

Difficulty Levels:
- Easy: Wide timing window (500ms), slow indicators
- Medium: Moderate timing (350ms), faster indicators
- Hard: Tight timing (200ms), fastest indicators
"""

from typing import Dict, Any
from dataclasses import dataclass
import asyncio

from .base import MinigameTrainer, MinigameConfig, TrainerState


@dataclass
class DanceGameConfig(MinigameConfig):
    """Configuration specific to the Dance Game trainer."""

    # Arrow detection thresholds
    detection_zone_start: float = 0.7  # % of screen height where arrows appear
    detection_zone_end: float = 0.3  # % of screen height for target zone

    # Timing fine-tuning
    pre_press_offset_ms: int = 30  # Press slightly early to account for input lag
    hold_duration_ms: int = 50  # How long to hold the key

    # Game-specific
    arrows_per_round: int = 20  # Approximate arrows per game
    round_timeout_sec: int = 120  # Max time for a round


class DanceGameTrainer(MinigameTrainer):
    """
    Trainer for the Wizard101 Pet Dance minigame.

    Usage via game_automation IPC:
        game.trainer.start name=dance difficulty=medium
        game.trainer.stop name=dance
        game.trainer.status name=dance
    """

    TRAINER_NAME = "dance"
    TRAINER_VERSION = "1.0.0"

    # Arrow key mappings
    ARROW_KEYS = {"up": "UP", "down": "DOWN", "left": "LEFT", "right": "RIGHT"}

    def __init__(self, config: DanceGameConfig, wizard_adapter: Any):
        super().__init__(config, wizard_adapter)
        self.config: DanceGameConfig = config
        self._pending_arrows = []
        self._last_detection_time = 0

    async def _main_loop(self):
        """
        Main dance game automation loop.

        1. Query game state from Maelstrom (screenshot analysis)
        2. Detect incoming arrows and their positions
        3. Calculate timing based on arrow velocity
        4. Send keypress at optimal moment
        5. Track score and handle game-over
        """
        self.log("Dance game loop started", "info")
        round_start = asyncio.get_event_loop().time()

        try:
            while self._state == TrainerState.RUNNING:
                # Check for pause
                while self._state == TrainerState.PAUSED:
                    await asyncio.sleep(0.1)

                if self._state != TrainerState.RUNNING:
                    break

                # Check round timeout
                elapsed = asyncio.get_event_loop().time() - round_start
                if elapsed > self.config.round_timeout_sec:
                    self.log("Round timeout reached", "warning")
                    break

                # Get current game state
                game_state = await self._detect_game_state()

                # Handle game over
                if game_state.get("game_over"):
                    self.log(f"Game over - Score: {self._score}", "info")
                    self._attempts += 1

                    if game_state.get("success"):
                        self._successes += 1

                    if (
                        self.config.auto_retry
                        and self._attempts < self.config.max_retries
                    ):
                        await self._start_new_round()
                        round_start = asyncio.get_event_loop().time()
                        continue
                    else:
                        break

                # Process detected arrows
                arrows = game_state.get("arrows", [])
                for arrow in arrows:
                    if await self._should_press(arrow):
                        success = await self._execute_action(
                            "press", direction=arrow["direction"]
                        )
                        if success:
                            self._score += 1

                # Poll at ~60 FPS to catch fast arrows
                await asyncio.sleep(0.016)

        except asyncio.CancelledError:
            self.log("Loop cancelled", "debug")
            raise
        except Exception as e:
            self._state = TrainerState.ERROR
            self.log(f"Loop error: {e}", "error")

        self.log(f"Dance loop ended - Final score: {self._score}", "info")

    async def _detect_game_state(self) -> Dict[str, Any]:
        """
        Detect current dance game state via Maelstrom.

        Queries the adapter for screenshot analysis to find:
        - Arrow indicators and their positions
        - Current score display
        - Game over screen
        """
        # If adapter not available, return mock state for testing
        if not self.adapter:
            return {"arrows": [], "game_over": False, "success": False}

        try:
            # Request game state from Maelstrom
            # This would use image recognition to analyze the game screen
            state = await self.adapter.get_game_state()

            if state.get("success"):
                return self._parse_dance_state(state.get("data", {}))
            else:
                return {"arrows": [], "game_over": False}

        except Exception as e:
            self.log(f"Detection error: {e}", "error")
            return {"arrows": [], "game_over": False}

    def _parse_dance_state(self, raw_state: Dict[str, Any]) -> Dict[str, Any]:
        """Parse raw Maelstrom state into dance game format."""
        # TODO: Implement actual parsing when Maelstrom provides data
        # This would extract arrow positions, directions, and timing
        return {
            "arrows": raw_state.get("arrows", []),
            "game_over": raw_state.get("game_over", False),
            "success": raw_state.get("success", False),
            "score": raw_state.get("score", 0),
        }

    async def _should_press(self, arrow: Dict[str, Any]) -> bool:
        """
        Determine if it's time to press for this arrow.

        Based on arrow position and velocity, calculates if the arrow
        is in the target zone accounting for reaction time.
        """
        position = arrow.get("position", 0)  # 0-1 normalized

        # Arrow in target zone?
        target = self.config.detection_zone_end
        timing = self.config.get_timing()
        window = timing["window_ms"] / 1000.0  # Convert to seconds

        # Simple position-based check (would be velocity-based with real data)
        return position <= target + window

    async def _execute_action(self, action: str, **kwargs) -> bool:
        """Execute a game action (keypress)."""
        if action == "press":
            direction = kwargs.get("direction", "")
            key = self.ARROW_KEYS.get(direction.lower(), direction.upper())

            if self.adapter:
                result = await self.adapter.send_key(
                    key, self.config.hold_duration_ms / 1000.0
                )
                self.log(f"Pressed {direction} -> {result.get('success')}", "debug")
                return result.get("success", False)
            else:
                self.log(f"[MOCK] Would press {direction}", "debug")
                return True

        return False

    async def _start_new_round(self):
        """Start a new dance game round (retry)."""
        self.log("Starting new round...", "info")

        # Press interact to start new game
        if self.adapter:
            await self.adapter.interact()

        # Wait for game to initialize
        await asyncio.sleep(1.5)

    async def calibrate(self) -> Dict[str, Any]:
        """
        Calibrate timing for the dance game.

        Measures:
        - Screen detection latency
        - Input-to-display lag
        - Arrow velocity at current difficulty
        """
        self._state = TrainerState.CALIBRATING
        self.log("Calibrating dance game timing...", "info")

        # TODO: Implement real calibration with Maelstrom
        # This would:
        # 1. Detect a test arrow
        # 2. Measure time from detection to target zone
        # 3. Calculate optimal pre-press offset

        await asyncio.sleep(0.5)

        self._state = TrainerState.IDLE

        return {
            "success": True,
            "calibration": {
                "pre_press_offset_ms": self.config.pre_press_offset_ms,
                "hold_duration_ms": self.config.hold_duration_ms,
                "difficulty": self.config.difficulty,
                "timing_window_ms": self.config.get_timing()["window_ms"],
            },
            "message": "Calibration complete (using defaults - Maelstrom integration pending)",
        }

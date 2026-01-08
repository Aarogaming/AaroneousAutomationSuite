"""
Game Mode Manager - On-Demand Game Automation Context

This module provides a "Game Mode" abstraction that orchestrates the lifecycle
of game automation components. When entering game mode, it:
1. Starts Project Maelstrom (C# game client bridge)
2. Enables game automation plugins
3. Begins game state monitoring
4. Tracks activity for auto-idle timeout

Game mode is designed to be resource-efficient - heavy game automation
components only run when actively needed.

Usage:
    game_mode = GameModeManager(hub)
    await game_mode.enter()  # Start game automation
    # ... do game stuff ...
    await game_mode.exit()   # Clean shutdown
    
    # Or with auto-timeout:
    await game_mode.enter(idle_timeout_minutes=30)
"""

import asyncio
from datetime import datetime, timedelta
from enum import Enum
from typing import Dict, Any, Optional, List, Callable
from dataclasses import dataclass, field
from loguru import logger


class GameModeState(Enum):
    """Game mode states."""
    INACTIVE = "inactive"
    ENTERING = "entering"
    ACTIVE = "active"
    EXITING = "exiting"
    ERROR = "error"


class IdleMode(Enum):
    """
    What constitutes 'idle' for timeout purposes.
    
    - HUMAN_ONLY: Only human interaction resets idle timer (IPC commands, CLI)
    - AUTOMATION_AWARE: Trainer activity and Maelstrom commands also count
    - NEVER: Never idle out - disable timeout entirely
    """
    HUMAN_ONLY = "human_only"           # Only manual commands reset idle
    AUTOMATION_AWARE = "automation_aware"  # Any system activity resets idle
    NEVER = "never"                     # Never auto-exit (timeout disabled)


@dataclass
class GameModeConfig:
    """
    Configuration for game mode behavior.
    
    Idle Timeout Behavior:
        The idle_mode setting controls what resets the idle timer:
        
        - HUMAN_ONLY (default): Only explicit human interaction resets idle.
          Use when you want automation to run unattended but still timeout
          when the automation finishes.
          
        - AUTOMATION_AWARE: Any system activity resets idle - trainer cycles,
          Maelstrom commands, game events. Use for long-running unattended
          automation that should stay active as long as it's doing work.
          
        - NEVER: Never timeout. Game mode stays active until manual exit.
          Use for 24/7 operation or when managing timeout externally.
    """
    idle_timeout_minutes: int = 30       # Auto-exit after N minutes of inactivity
    idle_mode: str = "automation_aware"  # What counts as 'activity' (see IdleMode)
    auto_detect_game: bool = True        # Auto-enter when game window detected
    start_maelstrom: bool = True         # Start Maelstrom on enter
    enable_trainers: bool = True         # Enable minigame trainers on enter
    snapshot_interval_ms: int = 100      # Game state polling interval
    
    # Granular activity controls (when idle_mode = automation_aware)
    count_trainer_cycles: bool = True    # Trainer execution resets idle
    count_maelstrom_commands: bool = True  # Commands to Maelstrom reset idle
    count_game_events: bool = True       # Game state changes reset idle
    count_snapshots: bool = False        # Raw snapshots reset idle (noisy!)


@dataclass
class GameModeSession:
    """Tracks a game mode session."""
    started_at: datetime = field(default_factory=datetime.now)
    last_human_activity: datetime = field(default_factory=datetime.now)
    last_automation_activity: datetime = field(default_factory=datetime.now)
    trainers_started: List[str] = field(default_factory=list)
    commands_executed: int = 0
    snapshots_received: int = 0
    trainer_cycles: int = 0
    game_events_received: int = 0
    
    @property
    def duration_minutes(self) -> float:
        """Get session duration in minutes."""
        return (datetime.now() - self.started_at).total_seconds() / 60
    
    @property
    def human_idle_minutes(self) -> float:
        """Get time since last human interaction in minutes."""
        return (datetime.now() - self.last_human_activity).total_seconds() / 60
    
    @property
    def automation_idle_minutes(self) -> float:
        """Get time since any activity (human or automation) in minutes."""
        last_any = max(self.last_human_activity, self.last_automation_activity)
        return (datetime.now() - last_any).total_seconds() / 60
    
    # Legacy property for backward compatibility
    @property
    def idle_minutes(self) -> float:
        """Get idle time in minutes (automation-aware by default)."""
        return self.automation_idle_minutes
    
    @property
    def last_activity(self) -> datetime:
        """Get most recent activity timestamp (any type)."""
        return max(self.last_human_activity, self.last_automation_activity)
    
    def touch_human(self) -> None:
        """Record human interaction."""
        self.last_human_activity = datetime.now()
    
    def touch_automation(self) -> None:
        """Record automation activity."""
        self.last_automation_activity = datetime.now()
    
    def touch(self) -> None:
        """Update both activity timestamps (legacy compatibility)."""
        now = datetime.now()
        self.last_human_activity = now
        self.last_automation_activity = now


class GameModeManager:
    """
    Manages the game automation context lifecycle.
    
    Game Mode is an on-demand state where heavy game automation resources
    are active. This keeps the Hub lightweight when not gaming.
    """
    
    def __init__(self, hub: Any):
        self._hub = hub
        self._state = GameModeState.INACTIVE
        self._config = GameModeConfig()
        self._session: Optional[GameModeSession] = None
        self._idle_check_task: Optional[asyncio.Task] = None
        
        # Plugin references (populated on enter)
        self._maelstrom_plugin = None
        self._game_automation_plugin = None
        
        # Event callbacks
        self._on_enter_callbacks: List[Callable] = []
        self._on_exit_callbacks: List[Callable] = []
    
    @property
    def state(self) -> GameModeState:
        """Current game mode state."""
        return self._state
    
    @property
    def is_active(self) -> bool:
        """Check if game mode is active."""
        return self._state == GameModeState.ACTIVE
    
    @property
    def session(self) -> Optional[GameModeSession]:
        """Current session info (if active)."""
        return self._session
    
    def configure(self, **kwargs) -> None:
        """Update game mode configuration."""
        for key, value in kwargs.items():
            if hasattr(self._config, key):
                setattr(self._config, key, value)
                logger.debug(f"GameMode config: {key} = {value}")
    
    async def enter(
        self,
        idle_timeout_minutes: Optional[int] = None,
        start_maelstrom: Optional[bool] = None,
        enable_trainers: Optional[bool] = None
    ) -> Dict[str, Any]:
        """
        Enter game mode - start game automation components.
        
        Args:
            idle_timeout_minutes: Override idle timeout (0 = no timeout)
            start_maelstrom: Override whether to start Maelstrom
            enable_trainers: Override whether to enable trainers
            
        Returns:
            Result dict with success status and details
        """
        if self._state == GameModeState.ACTIVE:
            return {"success": False, "error": "Already in game mode"}
        
        if self._state in (GameModeState.ENTERING, GameModeState.EXITING):
            return {"success": False, "error": f"Transition in progress: {self._state.value}"}
        
        self._state = GameModeState.ENTERING
        logger.info("🎮 Entering game mode...")
        
        # Apply overrides
        timeout = idle_timeout_minutes if idle_timeout_minutes is not None else self._config.idle_timeout_minutes
        do_start_maelstrom = start_maelstrom if start_maelstrom is not None else self._config.start_maelstrom
        do_enable_trainers = enable_trainers if enable_trainers is not None else self._config.enable_trainers
        
        try:
            # Start session tracking
            self._session = GameModeSession()
            
            # Get plugin references
            await self._acquire_plugins()
            
            # Start Maelstrom if configured
            if do_start_maelstrom and self._maelstrom_plugin:
                logger.info("Starting Maelstrom...")
                result = await self._maelstrom_plugin.start_maelstrom()
                if not result.get("success"):
                    logger.warning(f"Maelstrom start failed: {result.get('error')}")
                    # Continue anyway - might already be running externally
            
            # Enable game automation features
            if do_enable_trainers and self._game_automation_plugin:
                logger.debug("Game automation plugin ready for trainers")
            
            # Start idle timeout checker (unless mode is 'never' or timeout is 0)
            idle_mode = self._config.idle_mode.lower()
            if timeout > 0 and idle_mode != IdleMode.NEVER.value:
                self._idle_check_task = asyncio.create_task(
                    self._idle_timeout_loop(timeout)
                )
                logger.debug(f"Idle timeout: {timeout}min ({idle_mode} mode)")
            else:
                logger.debug("Idle timeout disabled")
            
            self._state = GameModeState.ACTIVE
            
            # Fire enter callbacks
            for callback in self._on_enter_callbacks:
                try:
                    await callback() if asyncio.iscoroutinefunction(callback) else callback()
                except Exception as e:
                    logger.warning(f"Enter callback error: {e}")
            
            # Broadcast event
            await self._broadcast_event("game_mode_entered", {
                "idle_timeout_minutes": timeout,
                "maelstrom_started": do_start_maelstrom,
                "trainers_enabled": do_enable_trainers
            })
            
            logger.success("🎮 Game mode active!")
            return {
                "success": True,
                "message": "Game mode active",
                "idle_timeout_minutes": timeout,
                "session_started": self._session.started_at.isoformat()
            }
            
        except Exception as e:
            self._state = GameModeState.ERROR
            logger.error(f"Failed to enter game mode: {e}")
            return {"success": False, "error": str(e)}
    
    async def exit(self, reason: str = "manual") -> Dict[str, Any]:
        """
        Exit game mode - stop game automation components.
        
        Args:
            reason: Why we're exiting (manual, idle_timeout, error, etc.)
            
        Returns:
            Result dict with session summary
        """
        if self._state == GameModeState.INACTIVE:
            return {"success": False, "error": "Not in game mode"}
        
        if self._state == GameModeState.EXITING:
            return {"success": False, "error": "Already exiting"}
        
        self._state = GameModeState.EXITING
        logger.info(f"🎮 Exiting game mode (reason: {reason})...")
        
        try:
            # Cancel idle checker
            if self._idle_check_task:
                self._idle_check_task.cancel()
                try:
                    await self._idle_check_task
                except asyncio.CancelledError:
                    pass
                self._idle_check_task = None
            
            # Stop any running trainers
            if self._game_automation_plugin:
                # Get active trainers and stop them
                try:
                    status = await self._game_automation_plugin.handle_trainer_status()
                    for trainer_name in status.get("trainers", {}).keys():
                        await self._game_automation_plugin.handle_trainer_stop(trainer_name)
                except Exception as e:
                    logger.warning(f"Error stopping trainers: {e}")
            
            # Stop Maelstrom if we started it
            if self._maelstrom_plugin and self._config.start_maelstrom:
                logger.info("Stopping Maelstrom...")
                await self._maelstrom_plugin.stop_maelstrom()
            
            # Capture session summary
            session_summary = None
            if self._session:
                session_summary = {
                    "duration_minutes": round(self._session.duration_minutes, 2),
                    "commands_executed": self._session.commands_executed,
                    "snapshots_received": self._session.snapshots_received,
                    "trainers_used": self._session.trainers_started
                }
            
            # Fire exit callbacks
            for callback in self._on_exit_callbacks:
                try:
                    await callback() if asyncio.iscoroutinefunction(callback) else callback()
                except Exception as e:
                    logger.warning(f"Exit callback error: {e}")
            
            # Broadcast event
            await self._broadcast_event("game_mode_exited", {
                "reason": reason,
                "session": session_summary
            })
            
            self._session = None
            self._state = GameModeState.INACTIVE
            
            logger.success(f"🎮 Game mode exited. Session: {session_summary}")
            return {
                "success": True,
                "message": f"Game mode exited ({reason})",
                "session": session_summary
            }
            
        except Exception as e:
            self._state = GameModeState.ERROR
            logger.error(f"Error exiting game mode: {e}")
            return {"success": False, "error": str(e)}
    
    async def toggle(self) -> Dict[str, Any]:
        """Toggle game mode on/off."""
        if self.is_active:
            return await self.exit(reason="toggle")
        else:
            return await self.enter()
    
    def touch_activity(self, is_human: bool = True) -> None:
        """
        Record activity to reset idle timer.
        
        Args:
            is_human: True if this is human-initiated activity
        """
        if self._session:
            if is_human:
                self._session.touch_human()
            else:
                self._session.touch_automation()
    
    def record_command(self, is_human: bool = True) -> None:
        """
        Record a command execution.
        
        Args:
            is_human: True if command was triggered by human (CLI, IPC call)
        """
        if self._session:
            self._session.commands_executed += 1
            if is_human:
                self._session.touch_human()
            elif self._config.count_maelstrom_commands:
                self._session.touch_automation()
    
    def record_snapshot(self) -> None:
        """Record a snapshot received."""
        if self._session:
            self._session.snapshots_received += 1
            if self._config.count_snapshots:
                self._session.touch_automation()
    
    def record_trainer_cycle(self, trainer_name: str) -> None:
        """
        Record a trainer execution cycle (automation activity).
        
        This is called when a trainer completes a cycle of its work,
        indicating the system is actively running automation.
        """
        if self._session:
            self._session.trainer_cycles += 1
            if self._config.count_trainer_cycles:
                self._session.touch_automation()
    
    def record_game_event(self, event_type: str = "generic") -> None:
        """
        Record a game state event (automation activity).
        
        Args:
            event_type: Type of game event (for logging/stats)
        """
        if self._session:
            self._session.game_events_received += 1
            if self._config.count_game_events:
                self._session.touch_automation()
    
    def record_trainer_start(self, trainer_name: str) -> None:
        """Record a trainer being started (human action)."""
        if self._session and trainer_name not in self._session.trainers_started:
            self._session.trainers_started.append(trainer_name)
            self._session.touch_human()  # Starting a trainer is human-initiated
    
    def on_enter(self, callback: Callable) -> None:
        """Register a callback for when game mode is entered."""
        self._on_enter_callbacks.append(callback)
    
    def on_exit(self, callback: Callable) -> None:
        """Register a callback for when game mode is exited."""
        self._on_exit_callbacks.append(callback)
    
    def get_status(self) -> Dict[str, Any]:
        """Get current game mode status."""
        result = {
            "state": self._state.value,
            "is_active": self.is_active,
            "config": {
                "idle_timeout_minutes": self._config.idle_timeout_minutes,
                "idle_mode": self._config.idle_mode,
                "auto_detect_game": self._config.auto_detect_game,
                "start_maelstrom": self._config.start_maelstrom,
            }
        }
        
        if self._session:
            result["session"] = {
                "started_at": self._session.started_at.isoformat(),
                "duration_minutes": round(self._session.duration_minutes, 2),
                "human_idle_minutes": round(self._session.human_idle_minutes, 2),
                "automation_idle_minutes": round(self._session.automation_idle_minutes, 2),
                "commands_executed": self._session.commands_executed,
                "snapshots_received": self._session.snapshots_received,
                "trainer_cycles": self._session.trainer_cycles,
                "game_events": self._session.game_events_received,
                "trainers_started": self._session.trainers_started
            }
        
        return result
    
    # === Private Methods ===
    
    async def _acquire_plugins(self) -> None:
        """Get references to game-related plugins."""
        if hasattr(self._hub, 'plugin_registry'):
            registry = self._hub.plugin_registry
            
            # Get Maelstrom plugin
            if hasattr(registry, 'get_plugin'):
                self._maelstrom_plugin = registry.get_plugin('maelstrom')
                self._game_automation_plugin = registry.get_plugin('game_automation')
            elif hasattr(registry, 'plugins'):
                self._maelstrom_plugin = registry.plugins.get('maelstrom')
                self._game_automation_plugin = registry.plugins.get('game_automation')
        
        if not self._maelstrom_plugin:
            logger.warning("Maelstrom plugin not found - game bridge unavailable")
        if not self._game_automation_plugin:
            logger.warning("Game automation plugin not found - trainers unavailable")
    
    async def _idle_timeout_loop(self, timeout_minutes: int) -> None:
        """
        Background task to check for idle timeout.
        
        Respects the idle_mode setting:
        - HUMAN_ONLY: Only human_idle_minutes counts
        - AUTOMATION_AWARE: automation_idle_minutes counts (any activity)
        - NEVER: This loop is never started
        """
        check_interval = 60  # Check every minute
        
        try:
            while self.is_active:
                await asyncio.sleep(check_interval)
                
                if not self._session:
                    continue
                
                # Determine idle time based on mode
                idle_mode = self._config.idle_mode.lower()
                
                if idle_mode == IdleMode.NEVER.value:
                    # Should never get here, but just in case
                    continue
                elif idle_mode == IdleMode.HUMAN_ONLY.value:
                    idle_minutes = self._session.human_idle_minutes
                    idle_type = "human"
                else:  # AUTOMATION_AWARE (default)
                    idle_minutes = self._session.automation_idle_minutes
                    idle_type = "automation-aware"
                
                if idle_minutes >= timeout_minutes:
                    logger.info(
                        f"Game mode idle for {timeout_minutes} minutes "
                        f"({idle_type} mode), auto-exiting..."
                    )
                    await self.exit(reason=f"idle_timeout_{idle_type}")
                    break
                    
        except asyncio.CancelledError:
            pass
    
    async def _broadcast_event(self, event_type: str, data: Dict[str, Any]) -> None:
        """Broadcast a game mode event via Hub."""
        if hasattr(self._hub, 'broadcast_event'):
            await self._hub.broadcast_event(event_type, data)
        elif hasattr(self._hub, 'ws_manager') and hasattr(self._hub.ws_manager, 'broadcast'):
            await self._hub.ws_manager.broadcast({
                "type": event_type,
                "data": data
            })


# === IPC Command Handlers ===

def create_game_mode_handlers(game_mode: GameModeManager) -> Dict[str, Callable]:
    """
    Create IPC command handlers for game mode.
    
    Returns a dict of command -> handler function.
    """
    
    async def handle_enter(**kwargs) -> Dict[str, Any]:
        """Enter game mode."""
        return await game_mode.enter(**kwargs)
    
    async def handle_exit(reason: str = "manual") -> Dict[str, Any]:
        """Exit game mode."""
        return await game_mode.exit(reason=reason)
    
    async def handle_toggle() -> Dict[str, Any]:
        """Toggle game mode."""
        return await game_mode.toggle()
    
    async def handle_status() -> Dict[str, Any]:
        """Get game mode status."""
        return {"success": True, **game_mode.get_status()}
    
    async def handle_configure(**kwargs) -> Dict[str, Any]:
        """Configure game mode settings."""
        game_mode.configure(**kwargs)
        return {"success": True, "config": game_mode._config.__dict__}
    
    return {
        "hub.game_mode.enter": handle_enter,
        "hub.game_mode.exit": handle_exit,
        "hub.game_mode.toggle": handle_toggle,
        "hub.game_mode.status": handle_status,
        "hub.game_mode.configure": handle_configure,
    }

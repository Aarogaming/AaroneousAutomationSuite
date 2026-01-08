"""
Maelstrom Plugin - Project Maelstrom Integration

This plugin manages the lifecycle of Project Maelstrom (C# game client) and
bridges communication between the AAS Hub and the game automation layer.

Architecture:
    AAS Hub (Python) <--gRPC--> Project Maelstrom (C#) <--Win32--> Wizard101

Features:
- Auto-discovery of Maelstrom installation
- Process lifecycle management (start/stop/restart)
- Sub-plugin enumeration (bots, tools)
- Snapshot relay to WebSocket bus
- Health monitoring and auto-restart

Environment Variables:
- MAELSTROM_ROOT: Path to Maelstrom installation
- MAELSTROM_START_CMD: Override launch command
- MAELSTROM_AUTO_LAUNCH: Auto-start with Hub (true/false)
"""

import os
import sys
import json
import asyncio
import subprocess
from pathlib import Path
from typing import Dict, Any, Optional, List
from dataclasses import dataclass, field
from enum import Enum
from loguru import logger

from core.plugin_base import PluginBase
from core.config import AASConfig


class MaelstromState(Enum):
    """Maelstrom process states."""
    UNKNOWN = "unknown"
    STOPPED = "stopped"
    STARTING = "starting"
    RUNNING = "running"
    STOPPING = "stopping"
    ERROR = "error"


@dataclass
class MaelstromSubPlugin:
    """Represents a Maelstrom sub-plugin (bot/tool)."""
    name: str
    description: str
    entry: str
    enabled: bool = False
    path: Optional[Path] = None


@dataclass
class MaelstromSnapshot:
    """Game state snapshot from Maelstrom."""
    bot: str = ""
    status: str = "idle"
    health: Dict[str, Any] = field(default_factory=dict)
    position: Dict[str, float] = field(default_factory=dict)
    timestamp: int = 0


class MaelstromPlugin(PluginBase):
    """
    Plugin for managing Project Maelstrom C# game client.
    
    Handles:
    - Process lifecycle (start, stop, restart)
    - gRPC communication via Bridge service
    - Sub-plugin discovery and management
    - Snapshot relay to Hub WebSocket
    """
    
    version = "0.1.0"
    
    # Common Maelstrom installation paths
    COMMON_PATHS = [
        Path(os.environ.get("LOCALAPPDATA", "")) / "ProjectMaelstrom",
        Path(os.environ.get("PROGRAMFILES", "")) / "ProjectMaelstrom",
        Path.home() / "ProjectMaelstrom",
    ]
    
    def __init__(self, config: AASConfig, hub: Any):
        super().__init__("maelstrom", config, hub)
        
        # Process management
        self._process: Optional[subprocess.Popen] = None
        self._state = MaelstromState.UNKNOWN
        self._maelstrom_root: Optional[Path] = None
        self._executable: Optional[Path] = None
        
        # Sub-plugins
        self._sub_plugins: Dict[str, MaelstromSubPlugin] = {}
        
        # Snapshot cache
        self._latest_snapshot: Optional[MaelstromSnapshot] = None
        self._snapshot_task: Optional[asyncio.Task] = None
        
        # gRPC stub (for outbound calls to Maelstrom if it hosts a server)
        self._grpc_channel = None
        self._grpc_stub = None
    
    async def setup(self) -> None:
        """Initialize Maelstrom plugin."""
        logger.info("Initializing Maelstrom plugin...")
        
        # Discover Maelstrom installation
        self._discover_installation()
        
        # Register IPC handlers
        self._register_ipc_handlers()
        
        # Enumerate sub-plugins
        if self._maelstrom_root:
            self._enumerate_sub_plugins()
        
        # Auto-launch if configured
        auto_launch = os.environ.get("MAELSTROM_AUTO_LAUNCH", "false").lower() == "true"
        if auto_launch and self._executable:
            logger.info("Auto-launching Maelstrom...")
            await self.start_maelstrom()
        
        self._state = MaelstromState.STOPPED if not self._process else MaelstromState.RUNNING
        logger.success(f"Maelstrom plugin initialized. Root: {self._maelstrom_root}")
    
    async def shutdown(self) -> None:
        """Cleanup Maelstrom plugin."""
        logger.info("Shutting down Maelstrom plugin...")
        
        # Stop snapshot relay
        if self._snapshot_task:
            self._snapshot_task.cancel()
            try:
                await self._snapshot_task
            except asyncio.CancelledError:
                pass
        
        # Stop Maelstrom process
        if self._process:
            await self.stop_maelstrom()
        
        # Close gRPC channel
        if self._grpc_channel:
            await self._grpc_channel.close()
        
        logger.info("Maelstrom plugin shutdown complete.")
    
    def _discover_installation(self) -> None:
        """Find Maelstrom installation directory."""
        # Check environment variable first
        env_root = os.environ.get("MAELSTROM_ROOT")
        if env_root:
            path = Path(env_root)
            if path.exists():
                self._maelstrom_root = path
                logger.info(f"Found Maelstrom via MAELSTROM_ROOT: {path}")
        
        # Check common paths
        if not self._maelstrom_root:
            for path in self.COMMON_PATHS:
                if path.exists():
                    self._maelstrom_root = path
                    logger.info(f"Found Maelstrom at: {path}")
                    break
        
        # Check workspace-relative path
        if not self._maelstrom_root:
            workspace_path = Path(__file__).parent.parent.parent / "ProjectMaelstrom"
            if workspace_path.exists():
                self._maelstrom_root = workspace_path
                logger.info(f"Found Maelstrom in workspace: {workspace_path}")
        
        # Find executable
        if self._maelstrom_root:
            self._find_executable()
        else:
            logger.warning("Maelstrom installation not found. Set MAELSTROM_ROOT.")
    
    def _find_executable(self) -> None:
        """Locate the Maelstrom executable."""
        if not self._maelstrom_root:
            return
        
        # Check for override command
        start_cmd = os.environ.get("MAELSTROM_START_CMD")
        if start_cmd:
            self._executable = Path(start_cmd)
            return
        
        # Common executable locations
        candidates = [
            self._maelstrom_root / "ProjectMaelstrom.exe",
            self._maelstrom_root / "publish" / "win-x64" / "ProjectMaelstrom.exe",
            self._maelstrom_root / "bin" / "Release" / "net8.0" / "ProjectMaelstrom.exe",
            self._maelstrom_root / "bin" / "Debug" / "net8.0" / "ProjectMaelstrom.exe",
        ]
        
        for candidate in candidates:
            if candidate.exists():
                self._executable = candidate
                logger.debug(f"Found Maelstrom executable: {candidate}")
                return
        
        logger.warning("Maelstrom executable not found. May need to build or set MAELSTROM_START_CMD.")
    
    def _enumerate_sub_plugins(self) -> None:
        """Discover Maelstrom sub-plugins (bots/tools)."""
        if not self._maelstrom_root:
            return
        
        plugins_dir = self._maelstrom_root / "Plugins"
        if not plugins_dir.exists():
            logger.debug("No Maelstrom Plugins directory found.")
            return
        
        for plugin_path in plugins_dir.iterdir():
            if not plugin_path.is_dir():
                continue
            
            manifest_path = plugin_path / "plugin.json"
            if manifest_path.exists():
                try:
                    with open(manifest_path, "r") as f:
                        manifest = json.load(f)
                    
                    sub_plugin = MaelstromSubPlugin(
                        name=manifest.get("name", plugin_path.name),
                        description=manifest.get("description", ""),
                        entry=manifest.get("entry", ""),
                        path=plugin_path
                    )
                    self._sub_plugins[sub_plugin.name] = sub_plugin
                    logger.debug(f"Discovered Maelstrom sub-plugin: {sub_plugin.name}")
                except Exception as e:
                    logger.warning(f"Failed to load sub-plugin manifest {manifest_path}: {e}")
            else:
                # Register by folder name
                sub_plugin = MaelstromSubPlugin(
                    name=plugin_path.name,
                    description=f"Maelstrom plugin: {plugin_path.name}",
                    entry="",
                    path=plugin_path
                )
                self._sub_plugins[sub_plugin.name] = sub_plugin
        
        logger.info(f"Discovered {len(self._sub_plugins)} Maelstrom sub-plugins.")
    
    def _register_ipc_handlers(self) -> None:
        """Register IPC command handlers."""
        if not self._hub:
            return
        
        handlers = {
            'maelstrom.status': self.handle_status,
            'maelstrom.start': self.handle_start,
            'maelstrom.stop': self.handle_stop,
            'maelstrom.restart': self.handle_restart,
            'maelstrom.snapshot': self.handle_snapshot,
            'maelstrom.plugins.list': self.handle_plugins_list,
            'maelstrom.plugins.enable': self.handle_plugin_enable,
            'maelstrom.plugins.disable': self.handle_plugin_disable,
            'maelstrom.execute': self.handle_execute_command,
        }
        
        for cmd, handler in handlers.items():
            if hasattr(self._hub, 'register_ipc_handler'):
                self._hub.register_ipc_handler(cmd, handler)
    
    # === Process Management ===
    
    async def start_maelstrom(self) -> Dict[str, Any]:
        """Start the Maelstrom process."""
        if self._process and self._process.poll() is None:
            return {"success": False, "error": "Maelstrom already running"}
        
        if not self._executable or not self._executable.exists():
            return {"success": False, "error": "Maelstrom executable not found"}
        
        try:
            self._state = MaelstromState.STARTING
            logger.info(f"Starting Maelstrom: {self._executable}")
            
            # Start process
            self._process = subprocess.Popen(
                [str(self._executable)],
                cwd=str(self._maelstrom_root),
                stdout=subprocess.PIPE,
                stderr=subprocess.PIPE,
                creationflags=subprocess.CREATE_NEW_PROCESS_GROUP if sys.platform == "win32" else 0
            )
            
            # Wait briefly to check if it started
            await asyncio.sleep(1.0)
            
            if self._process.poll() is not None:
                stderr = self._process.stderr.read().decode() if self._process.stderr else ""
                self._state = MaelstromState.ERROR
                return {"success": False, "error": f"Process exited immediately: {stderr}"}
            
            self._state = MaelstromState.RUNNING
            
            # Broadcast event
            await self.broadcast_event("maelstrom_started", {
                "pid": self._process.pid,
                "executable": str(self._executable)
            })
            
            logger.success(f"Maelstrom started (PID: {self._process.pid})")
            return {"success": True, "pid": self._process.pid}
            
        except Exception as e:
            self._state = MaelstromState.ERROR
            logger.error(f"Failed to start Maelstrom: {e}")
            return {"success": False, "error": str(e)}
    
    async def stop_maelstrom(self) -> Dict[str, Any]:
        """Stop the Maelstrom process."""
        if not self._process:
            return {"success": False, "error": "Maelstrom not running"}
        
        try:
            self._state = MaelstromState.STOPPING
            pid = self._process.pid
            
            # Try graceful shutdown first
            self._process.terminate()
            
            # Wait for process to exit
            try:
                self._process.wait(timeout=5.0)
            except subprocess.TimeoutExpired:
                logger.warning("Maelstrom did not terminate gracefully, killing...")
                self._process.kill()
                self._process.wait()
            
            self._process = None
            self._state = MaelstromState.STOPPED
            
            # Broadcast event
            await self.broadcast_event("maelstrom_stopped", {"pid": pid})
            
            logger.info(f"Maelstrom stopped (was PID: {pid})")
            return {"success": True}
            
        except Exception as e:
            self._state = MaelstromState.ERROR
            logger.error(f"Failed to stop Maelstrom: {e}")
            return {"success": False, "error": str(e)}
    
    async def restart_maelstrom(self) -> Dict[str, Any]:
        """Restart the Maelstrom process."""
        stop_result = await self.stop_maelstrom()
        if not stop_result.get("success") and "not running" not in stop_result.get("error", ""):
            return stop_result
        
        await asyncio.sleep(0.5)
        return await self.start_maelstrom()
    
    # === IPC Handlers ===
    
    async def handle_status(self) -> Dict[str, Any]:
        """Get Maelstrom status."""
        is_running = self._process and self._process.poll() is None
        
        return {
            "success": True,
            "state": self._state.value,
            "running": is_running,
            "pid": self._process.pid if is_running else None,
            "root": str(self._maelstrom_root) if self._maelstrom_root else None,
            "executable": str(self._executable) if self._executable else None,
            "sub_plugins": len(self._sub_plugins),
            "latest_snapshot": self._latest_snapshot.__dict__ if self._latest_snapshot else None
        }
    
    async def handle_start(self) -> Dict[str, Any]:
        """Handle start command."""
        return await self.start_maelstrom()
    
    async def handle_stop(self) -> Dict[str, Any]:
        """Handle stop command."""
        return await self.stop_maelstrom()
    
    async def handle_restart(self) -> Dict[str, Any]:
        """Handle restart command."""
        return await self.restart_maelstrom()
    
    async def handle_snapshot(self) -> Dict[str, Any]:
        """Get latest snapshot."""
        if self._latest_snapshot:
            return {"success": True, **self._latest_snapshot.__dict__}
        return {"success": False, "error": "No snapshot available"}
    
    async def handle_plugins_list(self) -> Dict[str, Any]:
        """List Maelstrom sub-plugins."""
        plugins = [
            {
                "name": p.name,
                "description": p.description,
                "enabled": p.enabled,
                "path": str(p.path) if p.path else None
            }
            for p in self._sub_plugins.values()
        ]
        return {"success": True, "plugins": plugins}
    
    async def handle_plugin_enable(self, name: str) -> Dict[str, Any]:
        """Enable a Maelstrom sub-plugin."""
        if name not in self._sub_plugins:
            return {"success": False, "error": f"Plugin '{name}' not found"}
        
        self._sub_plugins[name].enabled = True
        # TODO: Send enable command to Maelstrom via gRPC
        return {"success": True, "message": f"Plugin '{name}' enabled"}
    
    async def handle_plugin_disable(self, name: str) -> Dict[str, Any]:
        """Disable a Maelstrom sub-plugin."""
        if name not in self._sub_plugins:
            return {"success": False, "error": f"Plugin '{name}' not found"}
        
        self._sub_plugins[name].enabled = False
        # TODO: Send disable command to Maelstrom via gRPC
        return {"success": True, "message": f"Plugin '{name}' disabled"}
    
    async def handle_execute_command(
        self, 
        command_type: str, 
        payload: Optional[str] = None
    ) -> Dict[str, Any]:
        """
        Execute a command via Maelstrom.
        
        This is the primary interface for game automation commands.
        Commands are forwarded to Maelstrom via gRPC.
        """
        if self._state != MaelstromState.RUNNING:
            return {"success": False, "error": f"Maelstrom not running (state: {self._state.value})"}
        
        # TODO: Implement gRPC client call to Maelstrom
        # For now, log and acknowledge
        logger.info(f"[Maelstrom] Execute: {command_type} | Payload: {payload}")
        
        return {
            "success": True,
            "message": f"Command '{command_type}' queued for Maelstrom",
            "note": "gRPC client not yet implemented"
        }
    
    # === Snapshot Handling ===
    
    async def receive_snapshot(self, snapshot_data: Dict[str, Any]) -> None:
        """
        Receive a snapshot from Maelstrom (called via IPC ExecuteCommand).
        
        This is triggered when Maelstrom sends MAELSTROM_SNAPSHOT commands.
        """
        self._latest_snapshot = MaelstromSnapshot(
            bot=snapshot_data.get("bot", ""),
            status=snapshot_data.get("status", "idle"),
            health=snapshot_data.get("health", {}),
            position=snapshot_data.get("position", {}),
            timestamp=snapshot_data.get("updated_at", 0)
        )
        
        # Broadcast to WebSocket
        await self.broadcast_event("maelstrom_snapshot", snapshot_data)
    
    # === Public API ===
    
    def get_info(self) -> Dict[str, Any]:
        """Return plugin metadata."""
        return {
            **super().get_info(),
            "state": self._state.value,
            "maelstrom_root": str(self._maelstrom_root) if self._maelstrom_root else None,
            "executable_found": self._executable is not None,
            "sub_plugins": list(self._sub_plugins.keys()),
        }
    
    @property
    def is_running(self) -> bool:
        """Check if Maelstrom process is running."""
        return self._process is not None and self._process.poll() is None


def register(hub: Any) -> MaelstromPlugin:
    """
    Factory function for plugin registration.
    Called by the Hub's plugin loader.
    """
    config = hub.config if hasattr(hub, 'config') else AASConfig()
    plugin = MaelstromPlugin(config, hub)
    return plugin

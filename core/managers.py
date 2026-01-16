from pathlib import Path
from typing import Optional
import os
from core.config import AASConfig, load_config


class ManagerHub:
    """
    Central hub for initializing and accessing all AAS managers.
    Ensures consistent configuration and reduces boilerplate.

    Usage:
        hub = ManagerHub.create()
        hub.tasks.claim_task("AAS-123")
    """

    def __init__(self, config: Optional[AASConfig] = None):
        # Use load_config to handle environment variables and .env file properly
        self.config = config or load_config()
        self._task_manager = None
        self._guild_manager = None
        self._batch_manager = None
        self._database_manager = None
        self._workspace_manager = None
        self._collaboration_manager = None
        self._game_mode_manager = None
        self._maelstrom_heartbeat = None
        self._maelstrom_heartbeats = {}
        self._coordination_manager = None

    @classmethod
    def create(cls, config: Optional[AASConfig] = None):
        """Factory method for creating hub"""
        return cls(config=config)

    @property
    def tasks(self):
        if self._task_manager is None:
            from core.task_manager import TaskManager

            self._task_manager = TaskManager(
                config=self.config,
                db=self.db,
                workspace=self.workspace,
                batch=self._batch_manager,
                ws=self.ws,
            )
            if self._batch_manager is not None:
                self._task_manager.batch_manager = self._batch_manager
        return self._task_manager

    @property
    def guild(self):
        """Deprecated: Use .tasks instead."""
        return self.tasks

    @property
    def batch_manager(self):
        if self._batch_manager is None:
            from core.batch_manager import BatchManager

            self._batch_manager = BatchManager(config=self.config, ws_manager=self.ws)
        if (
            self._task_manager is not None
            and getattr(self._task_manager, "batch_manager", None) is None
        ):
            self._task_manager.batch_manager = self._batch_manager
        return self._batch_manager

    @property
    def batch(self):
        return self.batch_manager

    @property
    def db(self):
        if self._database_manager is None:
            from core.db_manager import DatabaseManager

            db_path = os.getenv("AAS_DB_PATH", "artifacts/aas.db")
            self._database_manager = DatabaseManager(db_path=db_path)
            self._database_manager.create_tables()
        return self._database_manager

    @property
    def workspace(self):
        if self._workspace_manager is None:
            from core.workspace_manager import WorkspaceCoordinator

            self._workspace_manager = WorkspaceCoordinator(workspace_root=".")
        return self._workspace_manager

    @property
    def collaboration(self):
        if self._collaboration_manager is None:
            from core.collaboration_manager import AgentCollaborationManager

            self._collaboration_manager = AgentCollaborationManager(
                db=self.db, config=self.config
            )
        return self._collaboration_manager

    @property
    def plugins(self):
        """Lightweight plugin registry for discovery and UI/CLI surfaces."""
        if not hasattr(self, "_plugins"):
            from core.plugin_registry import get_plugin_registry

            self._plugins = get_plugin_registry()
        return self._plugins

    @property
    def ipc(self):
        """Project Maelstrom IPC Service"""
        from core.ipc_server import BridgeService

        return BridgeService(db_manager=self.db)

    @property
    def grpc(self):
        """Hub gRPC Service"""
        from core.grpc_service import HubServiceHandler

        return HubServiceHandler(hub_manager=self)

    @property
    def health_aggregator(self):
        if not hasattr(self, "_health_aggregator"):
            from core.health_manager import HealthAggregator

            def task_stats():
                try:
                    _, tasks, _ = self.tasks.guild.parse_board()
                    queued = sum(1 for t in tasks if t.get("status") == "queued")
                    in_progress = sum(
                        1 for t in tasks if t.get("status") == "In Progress"
                    )
                    done = sum(1 for t in tasks if t.get("status") == "Done")
                    return {
                        "queued": queued,
                        "in_progress": in_progress,
                        "done": done,
                        "total": len(tasks),
                    }
                except Exception:
                    return {}

            def workspace_info():
                try:
                    artifacts_root = Path("artifacts")
                    large_files = []
                    max_results = 5
                    threshold_mb = 200
                    for root, _, files in os.walk(artifacts_root):
                        for name in files:
                            path = Path(root) / name
                            try:
                                size_mb = path.stat().st_size / (1024 * 1024)
                            except Exception:
                                continue
                            if size_mb >= threshold_mb:
                                large_files.append(
                                    {"path": str(path), "size_mb": round(size_mb, 2)}
                                )
                                if len(large_files) >= max_results:
                                    break
                        if len(large_files) >= max_results:
                            break
                    return {
                        "large_files": large_files,
                        "large_files_count": len(large_files),
                    }
                except Exception:
                    return {}

            def plugin_info():
                try:
                    plugins = self.plugins
                    return {"count": len(plugins)}
                except Exception:
                    return {}

            def batch_info():
                try:
                    if not self.batch_manager:
                        return {"enabled": False}
                    return {
                        "enabled": True,
                        "auto_monitor": self.config.batch_auto_monitor,
                    }
                except Exception:
                    return {}

            self._health_aggregator = HealthAggregator(
                db_manager=self.db,
                task_stats_provider=task_stats,
                workspace_provider=workspace_info,
                plugin_provider=plugin_info,
                batch_provider=batch_info,
            )
        return self._health_aggregator

    @property
    def ws(self):
        """WebSocket manager (if set)"""
        return getattr(self, "_ws", None)

    @ws.setter
    def ws(self, value):
        self._ws = value
        if self._task_manager is not None:
            self._task_manager.ws = value
        if self._batch_manager is not None:
            self._batch_manager.ws_manager = value

    @property
    def patch(self):
        if not hasattr(self, "_patch_manager"):
            from core.patch_manager import PatchManager

            self._patch_manager = PatchManager(hub=self)
        return self._patch_manager

    @property
    def game_mode(self):
        """Game Mode manager for on-demand Maelstrom/game automation lifecycle."""
        if self._game_mode_manager is None:
            from core.game_mode import GameModeManager

            self._game_mode_manager = GameModeManager(hub=self)
        return self._game_mode_manager

    @property
    def coordination(self):
        if self._coordination_manager is None:
            from core.coordination import CoordinationConfig, CoordinationManager

            self._coordination_manager = CoordinationManager(
                config=CoordinationConfig(),
                ws_manager=self.ws,
            )
        return self._coordination_manager

    def set_maelstrom_heartbeat(self, payload: dict) -> None:
        client_id = self._extract_maelstrom_client_id(payload)
        if client_id:
            self._maelstrom_heartbeats[client_id] = payload
        self._maelstrom_heartbeat = payload

    def get_maelstrom_heartbeat(
        self, client_id: Optional[str] = None
    ) -> Optional[dict]:
        if client_id:
            return self._maelstrom_heartbeats.get(client_id)
        return self._maelstrom_heartbeat

    def get_maelstrom_heartbeats(self) -> dict:
        return dict(self._maelstrom_heartbeats)

    @staticmethod
    def _extract_maelstrom_client_id(payload: dict) -> Optional[str]:
        if not isinstance(payload, dict):
            return None
        snapshot = (
            payload.get("payload")
            if isinstance(payload.get("payload"), dict)
            else payload
        )
        if not isinstance(snapshot, dict):
            return None
        for key in ("ClientId", "clientId", "client_id"):
            value = snapshot.get(key)
            if value:
                return str(value)
        return None

    def get_health_summary(self) -> dict:
        """Returns a combined health summary from all managers."""
        summary = self.health_aggregator.scan()
        # Inject game mode status
        try:
            gm_status = self.game_mode.get_status()
            summary["metrics"]["game_mode"] = {
                "active": gm_status.get("state") == "ACTIVE",
                "state": gm_status.get("state", "INACTIVE"),
                "session": gm_status.get("session"),
            }
            summary["components"]["game_mode"] = (
                "active" if gm_status.get("state") == "ACTIVE" else "inactive"
            )
        except Exception:
            summary["metrics"]["game_mode"] = {"active": False, "state": "INACTIVE"}
            summary["components"]["game_mode"] = "inactive"
        return summary

    def validate_all(self) -> dict:
        """Validates all managers."""
        return {"tasks": self.tasks.validate(), "db": self.db.engine is not None}

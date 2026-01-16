from typing import Dict, Any, Optional, Callable
from datetime import datetime
from loguru import logger

import psutil
import time
import os
import socket
import shutil
from pathlib import Path

try:
    import requests  # type: ignore
except Exception:  # pragma: no cover
    requests = None


class HealthAggregator:
    """
    Aggregates health metrics from various AAS components.
    """

    def __init__(
        self,
        db_manager=None,
        task_stats_provider: Optional[Callable[[], Dict[str, Any]]] = None,
        workspace_provider: Optional[Callable[[], Dict[str, Any]]] = None,
        plugin_provider: Optional[Callable[[], Dict[str, Any]]] = None,
        batch_provider: Optional[Callable[[], Dict[str, Any]]] = None,
    ):
        self.start_time = time.time()
        self._last_latency_check = 0.0
        self._last_latency_ms = None
        self._last_latency = "unknown"
        self._last_db_check = 0.0
        self._last_db_status = "unknown"
        self._db_manager = db_manager
        self._task_stats_provider = task_stats_provider
        self._workspace_provider = workspace_provider
        self._plugin_provider = plugin_provider
        self._batch_provider = batch_provider

    def scan(self) -> Dict[str, Any]:
        """
        Perform a full health scan of the system.
        """
        logger.debug("Performing system health scan...")

        # Get system metrics
        cpu_usage = psutil.cpu_percent(interval=None)
        memory = psutil.virtual_memory()

        # Network Latency check (ping a reliable external endpoint as proxy for internet health)
        now = time.time()
        latency = self._last_latency
        latency_ms = self._last_latency_ms
        skip_latency = os.getenv("AAS_HEALTH_SKIP_LATENCY", "").lower() in {
            "1",
            "true",
            "yes",
        }
        if skip_latency:
            latency = "skipped"
            latency_ms = None
        elif self._last_latency_check == 0.0 or (now - self._last_latency_check) >= 30:
            if requests is None:
                latency = "unavailable"
                latency_ms = None
            else:
                try:
                    start = time.time()
                    # Use a lightweight check that isn't our own health endpoint to avoid recursion
                    requests.head("https://www.google.com", timeout=1)
                    latency_ms = int((time.time() - start) * 1000)
                    latency = f"{latency_ms}ms"
                except Exception:
                    latency = "timeout"
                    latency_ms = None
            self._last_latency_check = now
            self._last_latency = latency
            self._last_latency_ms = latency_ms

        # Database check
        db_load = self._last_db_status
        if self._last_db_check == 0.0 or (now - self._last_db_check) >= 10:
            try:
                if self._db_manager is None:
                    from core.db_manager import get_db_manager

                    self._db_manager = get_db_manager()
                with self._db_manager.get_session() as session:
                    session.execute(__import__("sqlalchemy").text("SELECT 1"))
                db_load = "healthy"
            except Exception:
                db_load = "error"
            self._last_db_check = now
            self._last_db_status = db_load

        # Web/IPC probes (lightweight TCP checks with optional HTTP health)
        web_host = os.getenv("AAS_WEB_HOST", "127.0.0.1")
        web_port = int(os.getenv("AAS_WEB_PORT", "8000"))
        ipc_host = os.getenv("AAS_IPC_HOST", "127.0.0.1")
        ipc_port = int(os.getenv("AAS_IPC_PORT", "50051"))

        def check_tcp(host: str, port: int, timeout: float = 0.5) -> bool:
            try:
                with socket.create_connection((host, port), timeout=timeout):
                    return True
            except Exception:
                return False

        web_status = (
            "skipped"
            if os.getenv("AAS_HEALTH_SKIP_WEB", "").lower() in {"1", "true", "yes"}
            else "unknown"
        )
        ipc_status = (
            "skipped"
            if os.getenv("AAS_HEALTH_SKIP_IPC", "").lower() in {"1", "true", "yes"}
            else "unknown"
        )

        if web_status != "skipped":
            if requests is None:
                web_status = "healthy" if check_tcp(web_host, web_port) else "down"
            else:
                try:
                    resp = requests.get(
                        f"http://{web_host}:{web_port}/health", timeout=1
                    )
                    web_status = "healthy" if resp.status_code == 200 else "error"
                except Exception:
                    # If HTTP fails but TCP is up, treat as degraded but healthy enough
                    web_status = "healthy" if check_tcp(web_host, web_port) else "down"

        if ipc_status != "skipped":
            ipc_status = "healthy" if check_tcp(ipc_host, ipc_port) else "down"

        # Workspace / artifacts checks
        workspace_status = "healthy"
        artifacts_root = Path(os.getenv("AAS_ARTIFACTS_DIR", "artifacts")).resolve()
        writable = True
        disk_free_gb = None
        disk_free_pct = None

        try:
            artifacts_root.mkdir(parents=True, exist_ok=True)
            probe_path = artifacts_root / ".health_probe"
            probe_path.write_text("ok", encoding="utf-8")
            probe_path.unlink(missing_ok=True)
        except Exception:
            writable = False
            workspace_status = "error"

        try:
            usage = shutil.disk_usage(artifacts_root)
            disk_free_gb = round(usage.free / (1024 * 1024 * 1024), 2)
            disk_free_pct = int(usage.free / usage.total * 100)
            if disk_free_gb < 1 or disk_free_pct < 5:
                workspace_status = "warning"
        except Exception:
            workspace_status = "unknown"

        # Optional providers for richer suite coverage
        def safe_call(
            provider: Optional[Callable[[], Dict[str, Any]]]
        ) -> Dict[str, Any]:
            if not provider:
                return {}
            try:
                return provider() or {}
            except Exception as e:
                logger.warning(f"Health provider failed: {e}")
                return {"error": str(e)}

        task_stats = safe_call(self._task_stats_provider)
        workspace_extra = safe_call(self._workspace_provider)
        plugin_info = safe_call(self._plugin_provider)
        batch_info = safe_call(self._batch_provider)

        # Calculate uptime
        uptime_seconds = int(time.time() - self.start_time)
        days, rem = divmod(uptime_seconds, 86400)
        hours, rem = divmod(rem, 3600)
        minutes, seconds = divmod(rem, 60)
        uptime_str = f"{days}d {hours}h {minutes}m"

        # Calculate health score
        health_score = 100
        if latency in {"timeout", "unavailable"}:
            health_score -= 20
        elif latency_ms is not None and latency_ms > 500:
            health_score -= 10
        if db_load != "healthy":
            health_score -= 50
        if web_status in {"down", "error", "unknown"}:
            health_score -= 10
        if ipc_status in {"down", "error", "unknown"}:
            health_score -= 10
        if workspace_status in {"warning", "unknown"}:
            health_score -= 10
        if workspace_status == "error":
            health_score -= 30
        queued = task_stats.get("queued", 0)
        if queued > 50:
            health_score -= 5
        if cpu_usage > 90:
            health_score -= 10
        if memory.percent > 90:
            health_score -= 10
        health_score = max(0, health_score)

        if latency in {"timeout", "unavailable"}:
            network_progress = 0
        elif latency_ms is None:
            network_progress = 0
        elif latency_ms <= 50:
            network_progress = 100
        elif latency_ms <= 100:
            network_progress = 80
        elif latency_ms <= 200:
            network_progress = 60
        elif latency_ms <= 500:
            network_progress = 40
        else:
            network_progress = 20

        database_progress = 100 if db_load == "healthy" else 0
        if health_score >= 80:
            status = "healthy"
        elif health_score >= 50:
            status = "warning"
        else:
            status = "critical"

        # Maintain compatibility with callers expecting overall_status.
        return {
            "timestamp": datetime.now().isoformat(),
            "status": status,
            "overall_status": status,
            "health_score": f"{health_score}%",
            "uptime": uptime_str,
            "metrics": {
                "cpu_usage": f"{cpu_usage}%",
                "cpu_progress": cpu_usage,
                "memory_usage": f"{memory.percent}%",
                "memory_progress": memory.percent,
                "network_latency": latency,
                "network_progress": network_progress,
                "database_load": db_load,
                "database_progress": database_progress,
                "web_status": web_status,
                "ipc_status": ipc_status,
                "artifacts_writable": writable,
                "disk_free_gb": disk_free_gb,
                "disk_free_pct": disk_free_pct,
                "tasks": task_stats,
                "plugins": plugin_info,
                "batch": batch_info,
                "workspace_extra": workspace_extra,
            },
            "components": {
                "database": "connected" if db_load != "error" else "error",
                "web": web_status,
                "ipc": ipc_status,
                "task_manager": "active",
                "workspace": workspace_status,
            },
        }

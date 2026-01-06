from typing import Dict, Any, List
from datetime import datetime
from loguru import logger

import psutil
import time

class HealthAggregator:
    """
    Aggregates health metrics from various AAS components.
    """
    def __init__(self):
        self.start_time = time.time()
        self._last_latency_check = 0.0
        self._last_latency_ms = None
        self._last_latency = "unknown"
        self._last_db_check = 0.0
        self._last_db_status = "unknown"

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
        if self._last_latency_check == 0.0 or (now - self._last_latency_check) >= 30:
            try:
                import requests
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
                from core.db_manager import get_db_manager
                db = get_db_manager()
                with db.get_session() as session:
                    session.execute(__import__('sqlalchemy').text("SELECT 1"))
                db_load = "healthy"
            except Exception:
                db_load = "error"
            self._last_db_check = now
            self._last_db_status = db_load

        # Calculate uptime
        uptime_seconds = int(time.time() - self.start_time)
        days, rem = divmod(uptime_seconds, 86400)
        hours, rem = divmod(rem, 3600)
        minutes, seconds = divmod(rem, 60)
        uptime_str = f"{days}d {hours}h {minutes}m"

        # Calculate health score
        health_score = 100
        if latency == "timeout":
            health_score -= 20
        elif latency_ms is not None and latency_ms > 500:
            health_score -= 10
        if db_load != "healthy":
            health_score -= 50
        if cpu_usage > 90:
            health_score -= 10
        if memory.percent > 90:
            health_score -= 10
        health_score = max(0, health_score)

        if latency == "timeout" or latency_ms is None:
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
        
        return {
            "timestamp": datetime.now().isoformat(),
            "status": status,
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
            },
            "components": {
                "database": "connected" if db_load != "error" else "error",
                "task_manager": "active",
                "workspace": "clean"
            }
        }

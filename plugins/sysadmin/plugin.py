import psutil
import os
from typing import Dict, Any
from loguru import logger
from core.config.manager import AASConfig

class SysAdminPlugin:
    """
    Autonomous SysAdmin Plugin for AAS.
    Monitors system resources and performs basic maintenance.
    """
    def __init__(self, config: AASConfig):
        self.config = config
        logger.info("SysAdmin Plugin initialized.")

    def get_system_stats(self) -> Dict[str, Any]:
        """Returns current CPU, Memory, and Disk usage."""
        stats = {
            "cpu_percent": psutil.cpu_percent(interval=1),
            "memory_percent": psutil.virtual_memory().percent,
            "disk_usage": psutil.disk_usage('/').percent,
            "boot_time": psutil.boot_time()
        }
        logger.debug(f"System Stats: {stats}")
        return stats

    def check_health(self) -> Dict[str, Any]:
        """Performs a health check on the system."""
        stats = self.get_system_stats()
        issues = []
        
        if stats["cpu_percent"] > 90:
            issues.append("High CPU usage detected (>90%)")
        if stats["memory_percent"] > 90:
            issues.append("High Memory usage detected (>90%)")
        if stats["disk_usage"] > 95:
            issues.append("Critical Disk usage detected (>95%)")
            
        return {
            "status": "Healthy" if not issues else "Warning",
            "issues": issues,
            "stats": stats
        }

    def run_maintenance(self):
        """Placeholder for automated maintenance tasks."""
        logger.info("Running automated system maintenance...")
        # Example: Clear temp files, rotate logs, etc.

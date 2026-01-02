import psutil
from loguru import logger

class SystemMonitor:
    """
    Home Server Monitoring Plugin.
    Tracks CPU, RAM, and Disk usage for the AAS Hub.
    """
    def get_stats(self) -> dict:
        stats = {
            "cpu_percent": psutil.cpu_percent(interval=1),
            "memory_percent": psutil.virtual_memory().percent,
            "disk_usage": psutil.disk_usage("/").percent,
            "boot_time": psutil.boot_time()
        }
        logger.debug(f"SystemMonitor: CPU {stats['cpu_percent']}% | RAM {stats['memory_percent']}%")
        return stats

    def check_health(self) -> bool:
        """
        Returns True if system resources are within safe limits.
        """
        stats = self.get_stats()
        if stats["cpu_percent"] > 90 or stats["memory_percent"] > 90:
            logger.warning("SystemMonitor: High resource usage detected!")
            return False
        return True

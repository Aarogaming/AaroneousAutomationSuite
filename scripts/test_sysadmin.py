import os
import sys
from loguru import logger

# Add project root to path
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from core.config.manager import load_config
from plugins.sysadmin.plugin import SysAdminPlugin

def main():
    """
    Test script for SysAdmin Plugin.
    """
    logger.info("Testing Autonomous SysAdmin Plugin...")
    
    try:
        config = load_config()
        plugin = SysAdminPlugin(config)
        
        health = plugin.check_health()
        logger.info(f"System Health Status: {health['status']}")
        
        if health['issues']:
            for issue in health['issues']:
                logger.warning(f"Issue detected: {issue}")
        else:
            logger.success("No system issues detected.")
            
        stats = health['stats']
        logger.info(f"CPU: {stats['cpu_percent']}% | RAM: {stats['memory_percent']}% | Disk: {stats['disk_usage']}%")
        
        plugin.run_maintenance()
        
        logger.success("SysAdmin integration test completed.")
            
    except Exception as e:
        logger.error(f"SysAdmin test failed: {e}")

if __name__ == "__main__":
    main()

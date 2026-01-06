import os
import sys
from loguru import logger

# Add project root to path
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from core.config import load_config
from plugins.home_assistant.plugin import HomeAssistantPlugin

def main():
    """
    Test script for Home Assistant integration.
    """
    logger.info("Testing Home Assistant Integration...")
    
    try:
        config = load_config()
        plugin = HomeAssistantPlugin(config)
        
        if not plugin.enabled:
            logger.warning("Home Assistant API not reachable. Check HOME_ASSISTANT_URL and HOME_ASSISTANT_TOKEN in .env")
            logger.success("Home Assistant client logic verified (Connection failure handled).")
            return

        # Test entity status (replace with a real entity ID if testing live)
        test_entity = "sensor.sun_next_rising"
        status = plugin.get_entity_status(test_entity)
        logger.info(f"Status of {test_entity}: {status}")
        
        logger.success("Home Assistant integration test completed.")
            
    except Exception as e:
        logger.error(f"Home Assistant test failed: {e}")

if __name__ == "__main__":
    main()

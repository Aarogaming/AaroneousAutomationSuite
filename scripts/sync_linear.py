import os
import sys
from loguru import logger
from dotenv import load_dotenv

# Add project root to path
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from core.config.manager import load_config
from core.handoff.manager import HandoffManager

def main():
    """
    CLI tool to trigger bi-directional sync between local ACTIVE_TASKS.md and Linear.
    """
    logger.info("Starting Linear Bi-directional Sync...")
    
    try:
        config = load_config()
        if not config.linear_api_key or not config.linear_team_id:
            logger.error("Linear configuration missing. Please set LINEAR_API_KEY and LINEAR_TEAM_ID in .env")
            return

        manager = HandoffManager(config=config)
        
        # 1. Pull from Linear
        logger.info(f"Pulling tasks from Linear (Team: {config.linear_team_id})...")
        manager.sync_linear_tasks(config.linear_team_id)
        
        # 2. Push local updates to Linear
        logger.info("Pushing local updates to Linear...")
        manager.push_local_to_linear(config.linear_team_id)
        
        logger.success("Sync completed successfully.")
        
    except Exception as e:
        logger.exception(f"Sync failed: {e}")

if __name__ == "__main__":
    main()

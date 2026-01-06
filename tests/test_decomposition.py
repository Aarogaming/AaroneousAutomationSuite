import os
import sys
from loguru import logger

# Add project root to path
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from core.config import load_config
from core.handoff_manager import HandoffManager

def main():
    """
    Test script for agentic task decomposition.
    """
    logger.info("Testing Agentic Task Decomposition...")
    
    try:
        config = load_config()
        manager = HandoffManager(config=config)
        
        # Create a dummy complex task
        task_id = manager.add_task(
            priority="high",
            title="Build a Multi-Modal Research Agent",
            description="Create an agent that can process images, text, and web search to generate research reports.",
            task_type="research"
        )
        
        logger.info(f"Created test task: {task_id}")
        
        # Trigger decomposition
        logger.info("Triggering decomposition (this requires OPENAI_API_KEY)...")
        manager.decompose_task(task_id)
        
        logger.success("Decomposition test triggered. Check ACTIVE_TASKS.md for results.")
        
    except Exception as e:
        logger.error(f"Decomposition test failed: {e}")

if __name__ == "__main__":
    main()

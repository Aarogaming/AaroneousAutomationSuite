import os
import sys
import asyncio
from loguru import logger

# Add project root to path
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from core.config import load_config
from core.handoff.vision import VisionClient

async def main():
    """
    Test script for Multi-Modal Vision integration.
    """
    logger.info("Testing Multi-Modal Vision Support...")
    
    try:
        config = load_config()
        client = VisionClient(config)
        
        # Check for a sample screenshot
        sample_path = "game_manager/maelstrom/screenshots/sample.jpg"
        if not os.path.exists(sample_path):
            logger.warning(f"Sample screenshot not found at {sample_path}. Creating a dummy file for logic test.")
            os.makedirs(os.path.dirname(sample_path), exist_ok=True)
            with open(sample_path, "wb") as f:
                f.write(b"dummy image data")

        logger.info(f"Analyzing sample image: {sample_path}")
        
        # This will fail if the API key is invalid or dummy data is used,
        # but we want to verify the client logic.
        description = await client.describe_screenshot(sample_path)
        logger.info(f"Vision Response: {description}")
        
        logger.success("Vision integration test completed.")
            
    except Exception as e:
        logger.error(f"Vision test failed: {e}")

if __name__ == "__main__":
    asyncio.run(main())

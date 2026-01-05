import os
import sys
import asyncio
from loguru import logger

# Add project root to path
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from core.handoff.adapter import Wizard101Adapter

async def main():
    """
    Test script for Game Adapters.
    """
    logger.info("Testing Game Adapters...")
    
    # Mock gRPC stub
    class MockStub:
        async def ExecuteCommand(self, request):
            logger.info(f"Mock gRPC: Executing {request.command_type}")
            return type('obj', (object,), {'success': True, 'message': 'Mock success'})
            
    adapter = Wizard101Adapter(MockStub())
    
    logger.info("Testing Wizard101Adapter...")
    await adapter.find_window()
    await adapter.click(100, 200)
    await adapter.send_key("M")
    state = await adapter.get_state()
    logger.info(f"Current state: {state}")
    
    logger.success("Game Adapter logic verified.")

if __name__ == "__main__":
    asyncio.run(main())

import asyncio
from core.managers import ManagerHub
from loguru import logger

def failing_function(x, y):
    logger.info(f"Executing failing_function with {x}, {y}")
    raise ValueError("Simulated UI Failure: Element 'submit_button' not found")

async def test_self_healing():
    logger.info("Starting Self-Healing Test...")
    
    hub = ManagerHub.create()
    
    # 1. Test handle_failure directly
    logger.info("Testing handle_failure directly...")
    result = hub.self_healing.handle_failure("Simulated Environment Error", task_id="AAS-208")
    logger.info(f"Healing Result: {result['diagnostic_pack']}")
    
    # 2. Test wrap_execute
    logger.info("Testing wrap_execute...")
    try:
        hub.self_healing.wrap_execute(failing_function, 10, 20, task_id="AAS-208-WRAP")
    except RuntimeError as e:
        logger.info(f"Caught expected RuntimeError with healing context: {str(e)[:200]}...")

    logger.success("Self-Healing Test Completed Successfully!")

if __name__ == "__main__":
    asyncio.run(test_self_healing())

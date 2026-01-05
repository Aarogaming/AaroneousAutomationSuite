import asyncio
import sys
import os

# Add project root to path
sys.path.append(os.getcwd())

from core.managers.tasks import TaskManager
from core.database.models import TaskPriority

async def main():
    print("Initializing TaskManager...")
    tm = TaskManager()
    
    print("Starting BackgroundWorker...")
    await tm.start_worker()
    
    print("Enqueuing a test task...")
    # We'll use a dummy task ID for testing
    await tm.worker.enqueue("AAS-TEST", priority=TaskPriority.LOW)
    
    print("Waiting for task processing...")
    await asyncio.sleep(5)
    
    print("Stopping BackgroundWorker...")
    await tm.stop_worker()
    print("Test complete.")

if __name__ == "__main__":
    asyncio.run(main())

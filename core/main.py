import asyncio
from loguru import logger
from core.config.manager import load_config
from core.ipc.server import serve_ipc
from core.handoff.manager import HandoffManager

async def main():
    logger.info("Initializing Aaroneous Automation Suite (AAS) Hub...")
    
    # 1. Load Resilient Configuration
    try:
        config = load_config()
    except Exception:
        logger.critical("Failed to load configuration. Hub cannot start.")
        return

    # 2. Initialize Handoff Manager
    handoff = HandoffManager()
    handoff.generate_health_report()
    logger.info("Handoff Protocol active.")

    # 3. Start IPC Bridge
    ipc_task = asyncio.create_task(serve_ipc(port=config.ipc_port))

    logger.success("AAS Hub is now running and awaiting Maelstrom connection.")
    
    try:
        await asyncio.gather(ipc_task)
    except asyncio.CancelledError:
        logger.info("AAS Hub shutting down...")

if __name__ == "__main__":
    asyncio.run(main())

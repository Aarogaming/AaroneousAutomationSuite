import asyncio
from core.managers import ManagerHub
from core.protocol_manager import HandoffObject
from loguru import logger

async def test_handoff_protocol():
    logger.info("Starting Agent Handoff Protocol Test...")

    hub = ManagerHub.create()

    # 0. Ensure task exists (for foreign key)
    from core.db_repositories import TaskRepository
    with hub.db.get_session() as session:
        if not TaskRepository.get_by_id(session, "AAS-212"):
            TaskRepository.create(session, "AAS-212", "Implement Agent Handoff Protocol")

    # 1. Create a handoff object
    handoff = HandoffObject(
        task_id="AAS-212",
        source_agent="Sixth",
        target_agent="GitHub Copilot",
        context_summary="Implemented core protocol and DB persistence.",
        technical_details={"schema_version": "1.0", "db_table": "handoffs"},
        relevant_files=["core/managers/protocol.py", "core/database/models.py"],
        pending_actions=["Verify with test script", "Add CLI command"]
    )

    # 2. Relay the handoff
    logger.info("Relaying handoff...")
    hub.protocol.relay_handoff(handoff)

    # 3. Retrieve the handoff
    logger.info("Retrieving handoff context...")
    retrieved = hub.protocol.get_handoff_context("AAS-212")

    if retrieved:
        logger.info(f"Retrieved Handoff from {retrieved.source_agent}: {retrieved.context_summary}")
        assert retrieved.source_agent == "Sixth"
        assert retrieved.target_agent == "GitHub Copilot"
        # Check if any file contains 'protocol.py'
        assert any("protocol.py" in f for f in retrieved.relevant_files)
    else:
        logger.error("Failed to retrieve handoff context!")
        return

    logger.success("Agent Handoff Protocol Test Completed Successfully!")

if __name__ == "__main__":
    asyncio.run(test_handoff_protocol())

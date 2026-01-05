from typing import Optional, Any, Dict, List
from pydantic import BaseModel, Field
from datetime import datetime
from loguru import logger

class ManagerProtocol:
    """
    Base protocol for all AAS managers to ensure consistent interface.
    """
    def get_status(self) -> dict:
        """Return manager status."""
        return {}

    def validate(self) -> bool:
        """Validate manager state."""
        return True

class HandoffObject(BaseModel):
    """
    Standardized context sharing between specialized AI agents.
    """
    task_id: str
    source_agent: str
    target_agent: Optional[str] = None
    context_summary: str
    technical_details: Dict[str, Any] = Field(default_factory=dict)
    relevant_files: List[str] = Field(default_factory=list)
    pending_actions: List[str] = Field(default_factory=list)
    timestamp: datetime = Field(default_factory=datetime.utcnow)

class AgentHandoffProtocol:
    """
    Implementation of the Agent Handoff Protocol (AAS-212).
    """
    def __init__(self, hub: Any):
        self.hub = hub

    def relay_handoff(self, handoff: HandoffObject):
        """
        Relay handoff context to the target agent or store it for the next claimant.
        """
        logger.info(f"Relaying handoff from {handoff.source_agent} for task {handoff.task_id}")
        
        # 1. Store in database (Handoff Table)
        from core.database.repositories import HandoffRepository
        with self.hub.db.get_session() as session:
            HandoffRepository.create(
                session,
                task_id=handoff.task_id,
                source_agent=handoff.source_agent,
                target_agent=handoff.target_agent,
                context_summary=handoff.context_summary,
                technical_details=handoff.technical_details,
                relevant_files=handoff.relevant_files,
                pending_actions=handoff.pending_actions
            )

        # 2. Store in Knowledge Graph for semantic search
        if hasattr(self.hub, "knowledge"):
            self.hub.knowledge.index_task_result(
                task_id=handoff.task_id,
                success=True,
                output=f"Handoff Context: {handoff.context_summary}\nFiles: {handoff.relevant_files}"
            )
            
        logger.success(f"Handoff context for {handoff.task_id} persisted.")

    def get_handoff_context(self, task_id: str) -> Optional[HandoffObject]:
        """
        Retrieve the latest handoff context for a task.
        """
        from core.database.repositories import HandoffRepository
        with self.hub.db.get_session() as session:
            handoffs = HandoffRepository.get_by_task(session, task_id)
            if not handoffs:
                return None
            
            latest = handoffs[0]
            return HandoffObject(
                task_id=str(latest.task_id),
                source_agent=str(latest.source_agent),
                target_agent=str(latest.target_agent) if latest.target_agent else None,
                context_summary=str(latest.context_summary),
                technical_details=latest.technical_details if isinstance(latest.technical_details, dict) else {},
                relevant_files=latest.relevant_files if isinstance(latest.relevant_files, list) else [],
                pending_actions=latest.pending_actions if isinstance(latest.pending_actions, list) else [],
                timestamp=latest.created_at # type: ignore
            )

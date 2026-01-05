"""
Agent Collaboration Manager

Manages multi-agent coordination, help requests, and capability-based task matching.
Prevents conflicts through check-in/check-out and fine-grained locking.
"""

import uuid
from typing import Optional, Dict, Any, List
from datetime import datetime, timedelta
from loguru import logger

from core.database.manager import DatabaseManager
from core.database.models import (
    AgentSession, HelpRequest, TaskLock, Task
)
from core.managers.protocol import HandoffObject


# Agent capability profiles
AGENT_CAPABILITIES = {
    "GitHub Copilot": {
        "strengths": ["code_completion", "refactoring", "debugging", "documentation"],
        "languages": ["python", "typescript", "javascript", "c#"],
        "context_window": "large",
        "best_for": ["incremental_changes", "code_review", "quick_fixes"]
    },
    "ChatGPT": {
        "strengths": ["planning", "architecture", "research", "problem_solving"],
        "languages": ["python", "javascript", "general"],
        "context_window": "xlarge",
        "best_for": ["system_design", "complex_analysis", "multi_step_tasks"]
    },
    "Claude": {
        "strengths": ["analysis", "documentation", "testing", "code_generation"],
        "languages": ["python", "javascript", "markdown"],
        "context_window": "xxlarge",
        "best_for": ["large_refactors", "comprehensive_docs", "test_suites"]
    },
    "Sixth": {
        "strengths": ["analysis", "documentation", "testing", "code_generation", "system_management"],
        "languages": ["python", "javascript", "markdown", "c#"],
        "context_window": "xxlarge",
        "best_for": ["large_refactors", "comprehensive_docs", "test_suites", "private_features"]
    },
    "Cline": {
        "strengths": ["autonomous_execution", "file_operations", "shell_commands"],
        "languages": ["python", "javascript", "bash"],
        "context_window": "medium",
        "best_for": ["automation", "batch_operations", "file_management"]
    }
}


class AgentCollaborationManager:
    """
    Manages agent check-ins, help requests, and capability matching.
    
    Key features:
    - Check-in/check-out for session tracking
    - Task locking to prevent conflicts
    - Help request protocol for collaboration
    - Capability-based task matching
    """
    
    def __init__(self, db: DatabaseManager, config: Optional[Any] = None):
        """Initialize with database manager."""
        self.db = db
        self.config = config
        self.capabilities = AGENT_CAPABILITIES
    
    # ===== Check-In/Check-Out =====
    
    def check_in(
        self, 
        agent_name: str, 
        capabilities: Optional[Dict[str, Any]] = None,
        agent_version: Optional[str] = None
    ) -> str:
        """
        Register agent session and return session ID.
        
        Args:
            agent_name: Name of the agent (e.g., "GitHub Copilot")
            capabilities: Optional custom capability profile
            agent_version: Optional version string
            
        Returns:
            Session ID for tracking this agent's work
        """
        session_id = f"session-{uuid.uuid4().hex[:12]}"
        
        # Use default capabilities if not provided
        caps = capabilities or self.capabilities.get(agent_name, {
            "strengths": ["general"],
            "languages": ["python"],
            "context_window": "medium",
            "best_for": ["general_tasks"]
        })
        
        with self.db.get_session() as session:
            agent_session = AgentSession(
                id=session_id,
                agent_name=agent_name,
                agent_version=agent_version,
                capabilities=caps,
                status="active",
                checked_in_at=datetime.utcnow(),
                last_activity=datetime.utcnow()
            )
            session.add(agent_session)
            session.commit()
        
        logger.info(f"✅ {agent_name} checked in: {session_id}")
        self._print_agent_roster()
        return session_id
    
    def check_out(self, session_id: str):
        """
        Mark agent session as offline.
        
        Args:
            session_id: Session to terminate
        """
        with self.db.get_session() as session:
            agent_session = session.query(AgentSession).filter_by(id=session_id).first()
            if agent_session:
                agent_session.status = "offline"
                agent_session.last_activity = datetime.utcnow()
                session.commit()
                logger.info(f"👋 {agent_session.agent_name} checked out")
    
    def heartbeat(self, session_id: str):
        """
        Update agent session activity timestamp.
        
        Args:
            session_id: Session to update
        """
        with self.db.get_session() as session:
            agent_session = session.query(AgentSession).filter_by(id=session_id).first()
            if agent_session:
                agent_session.last_activity = datetime.utcnow()
                session.commit()
    
    def get_active_agents(self) -> List[Dict[str, Any]]:
        """
        Get list of currently active agents.
        
        Returns:
            List of agent info dicts
        """
        with self.db.get_session() as session:
            agents = session.query(AgentSession).filter_by(status="active").all()
            return [{
                "session_id": a.id,
                "agent_name": a.agent_name,
                "agent_version": a.agent_version,
                "capabilities": a.capabilities,
                "current_task": a.current_task_id,
                "active_tasks": a.active_tasks_count,
                "last_activity": a.last_activity.isoformat()
            } for a in agents]
    
    def _print_agent_roster(self):
        """Print current agent roster with capabilities."""
        agents = self.get_active_agents()
        if not agents:
            return
        
        print("\n🤝 Active Agent Roster:")
        for agent in agents:
            caps = agent["capabilities"]
            strengths = ", ".join(caps.get("strengths", [])[:3])
            task = f" [Working: {agent['current_task']}]" if agent["current_task"] else ""
            print(f"  • {agent['agent_name']}: {strengths}{task}")
        print()
    
    # ===== Task Locking =====
    
    def acquire_task_lock(
        self, 
        task_id: str, 
        session_id: str, 
        lock_type: str = "active",
        timeout_minutes: int = 60
    ) -> bool:
        """
        Acquire lock on a task.
        
        Args:
            task_id: Task to lock
            session_id: Agent session requesting lock
            lock_type: "active" (full control), "soft" (intent), "helper" (read)
            timeout_minutes: Auto-release timeout
            
        Returns:
            True if lock acquired, False if task already locked
        """
        with self.db.get_session() as session:
            # Check for existing active lock
            existing_lock = session.query(TaskLock).filter_by(
                task_id=task_id
            ).first()
            
            if existing_lock and existing_lock.session_id != session_id:
                # Check if lock is expired
                if existing_lock.expires_at < datetime.utcnow():
                    logger.warning(f"🔓 Removing expired lock on {task_id}")
                    session.delete(existing_lock)
                elif existing_lock.lock_type in ["active", "soft"]:
                    # Task already locked by another agent
                    lock_owner = session.query(AgentSession).filter_by(
                        id=existing_lock.session_id
                    ).first()
                    logger.warning(
                        f"❌ Task {task_id} already locked by {lock_owner.agent_name}"
                    )
                    return False
            
            # Acquire lock
            lock = TaskLock(
                task_id=task_id,
                session_id=session_id,
                lock_type=lock_type,
                acquired_at=datetime.utcnow(),
                expires_at=datetime.utcnow() + timedelta(minutes=timeout_minutes),
                last_heartbeat=datetime.utcnow()
            )
            session.merge(lock)  # Use merge to handle existing helper locks
            
            # Update agent session
            agent_session = session.query(AgentSession).filter_by(
                id=session_id
            ).first()
            if lock_type == "active":
                agent_session.current_task_id = task_id
                agent_session.active_tasks_count += 1
            
            session.commit()
            logger.info(f"🔒 {agent_session.agent_name} acquired {lock_type} lock on {task_id}")
            return True
    
    def release_task_lock(self, task_id: str, session_id: str):
        """
        Release lock on a task.
        
        Args:
            task_id: Task to unlock
            session_id: Session that owns the lock
        """
        with self.db.get_session() as session:
            lock = session.query(TaskLock).filter_by(
                task_id=task_id,
                session_id=session_id
            ).first()
            
            if lock:
                lock_type = lock.lock_type
                session.delete(lock)
                
                # Update agent session
                agent_session = session.query(AgentSession).filter_by(
                    id=session_id
                ).first()
                if lock_type == "active" and agent_session:
                    agent_session.current_task_id = None
                
                session.commit()
                logger.info(f"🔓 Released lock on {task_id}")
    
    # ===== Help Requests =====
    
    def request_help(
        self,
        task_id: str,
        requester_session_id: str,
        help_type: str,
        context: str,
        urgency: str = "medium",
        estimated_time: Optional[int] = None
    ) -> str:
        """
        Create a help request for a task.
        
        Args:
            task_id: Task needing help
            requester_session_id: Agent requesting help
            help_type: Type of help needed (code_review, debugging, architecture, testing)
            context: Description of what help is needed
            urgency: low, medium, high, critical
            estimated_time: Estimated minutes needed
            
        Returns:
            Help request ID
        """
        request_id = f"help-{uuid.uuid4().hex[:12]}"
        
        with self.db.get_session() as session:
            # Get requester info
            requester = session.query(AgentSession).filter_by(
                id=requester_session_id
            ).first()
            
            help_request = HelpRequest(
                id=request_id,
                task_id=task_id,
                requester_session_id=requester_session_id,
                help_type=help_type,
                context=context,
                urgency=urgency,
                estimated_time=estimated_time,
                status="open"
            )
            session.add(help_request)
            
            # Update requester stats
            if requester:
                requester.help_requests_count += 1
            
            session.commit()
        
        if requester:
            logger.info(f"🆘 {requester.agent_name} requesting {help_type} help on {task_id}")
        self._broadcast_help_request(request_id)
        return request_id
    
    def accept_help_request(
        self, 
        request_id: str, 
        helper_session_id: str,
        response_message: Optional[str] = None
    ) -> bool:
        """
        Accept a help request.
        
        Args:
            request_id: Help request to accept
            helper_session_id: Agent offering help
            response_message: Optional message to requester
            
        Returns:
            True if accepted successfully
        """
        with self.db.get_session() as session:
            help_request = session.query(HelpRequest).filter_by(id=request_id).first()
            
            if not help_request or help_request.status != "open":
                return False
            
            # Update help request
            help_request.helper_session_id = helper_session_id
            help_request.status = "accepted"
            help_request.accepted_at = datetime.utcnow()
            help_request.response_message = response_message
            
            # Acquire helper lock (non-exclusive for multiple helpers)
            task_lock = TaskLock(
                task_id=help_request.task_id,
                session_id=helper_session_id,
                lock_type="helper",
                acquired_at=datetime.utcnow(),
                expires_at=datetime.utcnow() + timedelta(hours=2),
                last_heartbeat=datetime.utcnow()
            )
            session.add(task_lock)
            
            session.commit()
            
            helper = session.query(AgentSession).filter_by(id=helper_session_id).first()
            requester = session.query(AgentSession).filter_by(
                id=help_request.requester_session_id
            ).first()
            
            if helper and requester:
                logger.success(f"🤝 {helper.agent_name} accepted help request from {requester.agent_name}")
            return True
    
    def complete_help_request(self, request_id: str, outcome: str):
        """
        Mark help request as completed.
        
        Args:
            request_id: Help request to complete
            outcome: Summary of outcome
        """
        with self.db.get_session() as session:
            help_request = session.query(HelpRequest).filter_by(id=request_id).first()
            
            if help_request:
                help_request.status = "completed"
                help_request.completed_at = datetime.utcnow()
                help_request.response_message = outcome
                
                # Release helper lock
                if help_request.helper_session_id:
                    lock = session.query(TaskLock).filter_by(
                        task_id=help_request.task_id,
                        session_id=help_request.helper_session_id,
                        lock_type="helper"
                    ).first()
                    if lock:
                        session.delete(lock)
                
                session.commit()
                logger.info(f"✅ Help request {request_id} completed")
    
    def get_open_help_requests(self) -> List[Dict[str, Any]]:
        """
        Get all open help requests.
        
        Returns:
            List of open help request dicts
        """
        with self.db.get_session() as session:
            requests = session.query(HelpRequest).filter_by(status="open").all()
            return [{
                "id": r.id,
                "task_id": r.task_id,
                "requester": r.requester.agent_name if r.requester else "Unknown",
                "help_type": r.help_type,
                "context": r.context,
                "urgency": r.urgency,
                "estimated_time": r.estimated_time,
                "created_at": r.created_at.isoformat()
            } for r in requests]
    
    def _broadcast_help_request(self, request_id: str):
        """Broadcast help request to available agents."""
        with self.db.get_session() as session:
            help_req = session.query(HelpRequest).filter_by(id=request_id).first()
            if not help_req:
                return
            
            print(f"\n🆘 Help Request Broadcast:")
            print(f"  Task: {help_req.task_id}")
            print(f"  Type: {help_req.help_type}")
            print(f"  Urgency: {help_req.urgency}")
            print(f"  Context: {help_req.context}")
            if help_req.estimated_time:
                print(f"  Estimated: {help_req.estimated_time}min")
            print(f"\n  Suggested helpers based on capabilities:")
            
            # Match capabilities
            active_agents = self.get_active_agents()
            for agent in active_agents:
                if agent["session_id"] == help_req.requester_session_id:
                    continue  # Skip requester
                
                caps = agent["capabilities"]
                match_score = self._calculate_capability_match(help_req.help_type, caps)
                if match_score > 0.5:
                    print(f"    ✓ {agent['agent_name']} (match: {int(match_score*100)}%)")
            print()
    
    # ===== Capability Matching =====
    
    def find_best_agent_for_task(
        self, 
        task_description: str,
        task_tags: Optional[List[str]] = None
    ) -> Optional[Dict[str, Any]]:
        """
        Find the best available agent for a task based on capabilities.
        
        Args:
            task_description: Task description text
            task_tags: Optional list of task tags
            
        Returns:
            Agent info with match score, or None if no agents available
        """
        active_agents = self.get_active_agents()
        if not active_agents:
            return None
        
        # Calculate match scores
        scored_agents = []
        for agent in active_agents:
            # Skip busy agents
            if agent["active_tasks"] >= 3:
                continue
            
            score = self._calculate_task_match(
                task_description, 
                task_tags or [],
                agent["capabilities"]
            )
            
            # Penalize agents already working
            workload_penalty = agent["active_tasks"] * 0.1
            final_score = max(0, score - workload_penalty)
            
            scored_agents.append({
                **agent,
                "match_score": final_score
            })
        
        if not scored_agents:
            return None
        
        # Return best match
        best_agent = max(scored_agents, key=lambda a: a["match_score"])
        return best_agent if best_agent["match_score"] > 0.3 else None
    
    def _calculate_capability_match(
        self, 
        help_type: str, 
        capabilities: Dict[str, Any]
    ) -> float:
        """Calculate how well agent capabilities match help request."""
        strengths = capabilities.get("strengths", [])
        best_for = capabilities.get("best_for", [])
        
        # Direct strength match
        if help_type in strengths:
            return 1.0
        
        # Best-for match
        if help_type in best_for:
            return 0.9
        
        # Partial matches
        help_keywords = set(help_type.split("_"))
        strength_keywords = set("_".join(strengths).split("_"))
        overlap = len(help_keywords & strength_keywords)
        
        if overlap > 0:
            return 0.5 + (overlap * 0.1)
        
        return 0.2  # Default low match
    
    def _calculate_task_match(
        self,
        task_description: str,
        task_tags: List[str],
        capabilities: Dict[str, Any]
    ) -> float:
        """Calculate how well agent capabilities match a task."""
        # Feature gating: only allow certain agents for private features if not in private mode
        is_private_task = "private" in task_description.lower() or "private" in task_tags
        if is_private_task and self.config and not getattr(self.config, "is_private_version", False):
            # If it's a private task but we're not in private mode, 
            # only allow agents with 'private_features' strength to even see it (or penalize heavily)
            if "private_features" not in capabilities.get("best_for", []):
                return 0.0

        score = 0.0
        
        # Check tags against best_for
        best_for = set(capabilities.get("best_for", []))
        tag_matches = len(set(task_tags) & best_for)
        score += tag_matches * 0.3
        
        # Check description keywords against strengths
        strengths = capabilities.get("strengths", [])
        desc_lower = task_description.lower()
        for strength in strengths:
            if strength.replace("_", " ") in desc_lower:
                score += 0.2
        
        # Bonus for large context window on complex tasks
        if len(task_description) > 500:
            context_size = capabilities.get("context_window", "medium")
            context_bonus = {
                "small": 0.0,
                "medium": 0.1,
                "large": 0.2,
                "xlarge": 0.3,
                "xxlarge": 0.4
            }.get(context_size, 0.1)
            score += context_bonus
        
        return min(1.0, score)

    def relay_handoff(self, handoff: HandoffObject):
        """
        Relay handoff context to the target agent or store it for the next claimant.
        Implementation for AAS-212.
        """
        logger.info(f"Relaying handoff from {handoff.source_agent} for task {handoff.task_id}")
        
        from core.database.repositories import HandoffRepository
        with self.db.get_session() as session:
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
        logger.success(f"Handoff context for {handoff.task_id} persisted via CollaborationManager.")

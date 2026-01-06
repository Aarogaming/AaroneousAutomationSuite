# Agent Collaboration System

## Overview
AAS supports multiple AI agents (GitHub Copilot, ChatGPT, Claude/Sixth, Cline) working simultaneously on tasks. This system prevents conflicts, enables help requests, and optimizes task assignment based on agent strengths.

## Core Concepts

### 1. Agent Check-In
When an agent starts working, it **checks in** with:
- **Identity**: Agent name and version
- **Capabilities**: Strengths and expertise areas
- **Availability**: Current workload and capacity
- **Session**: Unique session ID for tracking

### 2. Capability Profiles
Each agent declares its strengths:

```python
AGENT_CAPABILITIES = {
    "GitHub Copilot": {
        "strengths": ["code_completion", "refactoring", "debugging", "documentation"],
        "languages": ["python", "typescript", "javascript", "c#"],
        "context_window": "large",
        "best_for": ["incremental_changes", "code_review", "quick_fixes"]
    },
    "ChatGPT (o1)": {
        "strengths": ["planning", "architecture", "research", "problem_solving"],
        "languages": ["python", "javascript", "general"],
        "context_window": "xlarge",
        "best_for": ["system_design", "complex_analysis", "multi_step_tasks"]
    },
    "Claude (Sixth)": {
        "strengths": ["analysis", "documentation", "testing", "code_generation"],
        "languages": ["python", "javascript", "markdown"],
        "context_window": "xxlarge",
        "best_for": ["large_refactors", "comprehensive_docs", "test_suites"]
    },
    "Cline": {
        "strengths": ["autonomous_execution", "file_operations", "shell_commands"],
        "languages": ["python", "javascript", "bash"],
        "context_window": "medium",
        "best_for": ["automation", "batch_operations", "file_management"]
    }
}
```

### 3. Task Ownership
- **Active Lock**: Agent currently working on task (row-level DB lock)
- **Soft Lock**: Agent has checked in but not yet claimed (prevents race conditions)
- **Help Request**: Original owner remains, helper gets read access
- **Handoff**: Explicit transfer of ownership

### 4. Help Request Protocol
Agents can request help without losing ownership:

```python
# Agent A is stuck on a task
help_request = {
    "task_id": "AAS-105",
    "requester": "GitHub Copilot",
    "help_type": "code_review",  # or "debugging", "architecture", "testing"
    "context": "Need review of gRPC proto implementation",
    "urgency": "medium",
    "estimated_time": "15min"
}

# System broadcasts to available agents
# Agent B responds
help_response = {
    "helper": "Claude (Sixth)",
    "accepted": True,
    "availability": "immediate",
    "estimated_completion": "15min"
}
```

## Implementation

### Database Schema Extensions

```python
class AgentSession(Base):
    """Active agent session tracking."""
    __tablename__ = "agent_sessions"
    
    id = Column(String(50), primary_key=True)  # session-uuid
    agent_name = Column(String(50), nullable=False)
    agent_version = Column(String(20), nullable=True)
    capabilities = Column(JSON, nullable=False)  # Capability profile
    status = Column(String(20), nullable=False, default="active")  # active, idle, offline
    current_task_id = Column(String(20), ForeignKey("tasks.id"), nullable=True)
    
    # Session metadata
    checked_in_at = Column(DateTime, nullable=False, default=datetime.utcnow)
    last_activity = Column(DateTime, nullable=False, default=datetime.utcnow)
    heartbeat_interval = Column(Integer, default=300)  # 5 minutes
    
    # Workload tracking
    active_tasks_count = Column(Integer, default=0)
    completed_tasks_count = Column(Integer, default=0)
    help_requests_count = Column(Integer, default=0)
    
    def __repr__(self):
        return f"<AgentSession {self.agent_name} ({self.status})>"


class HelpRequest(Base):
    """Help request between agents."""
    __tablename__ = "help_requests"
    
    id = Column(String(50), primary_key=True)
    task_id = Column(String(20), ForeignKey("tasks.id"), nullable=False)
    requester_session_id = Column(String(50), ForeignKey("agent_sessions.id"), nullable=False)
    helper_session_id = Column(String(50), ForeignKey("agent_sessions.id"), nullable=True)
    
    # Request details
    help_type = Column(String(50), nullable=False)  # code_review, debugging, architecture, testing
    context = Column(Text, nullable=False)
    urgency = Column(String(20), default="medium")  # low, medium, high, critical
    estimated_time = Column(Integer, nullable=True)  # minutes
    
    # Status tracking
    status = Column(String(20), nullable=False, default="open")  # open, accepted, completed, cancelled
    response_message = Column(Text, nullable=True)
    
    # Timestamps
    created_at = Column(DateTime, nullable=False, default=datetime.utcnow)
    accepted_at = Column(DateTime, nullable=True)
    completed_at = Column(DateTime, nullable=True)
    
    # Relationships
    task = relationship("Task", foreign_keys=[task_id])
    requester = relationship("AgentSession", foreign_keys=[requester_session_id])
    helper = relationship("AgentSession", foreign_keys=[helper_session_id])
    
    def __repr__(self):
        return f"<HelpRequest {self.id}: {self.help_type} ({self.status})>"


class TaskLock(Base):
    """Fine-grained task locking for conflict prevention."""
    __tablename__ = "task_locks"
    
    task_id = Column(String(20), ForeignKey("tasks.id"), primary_key=True)
    session_id = Column(String(50), ForeignKey("agent_sessions.id"), nullable=False)
    lock_type = Column(String(20), nullable=False)  # "active", "soft", "helper"
    
    # Lock metadata
    acquired_at = Column(DateTime, nullable=False, default=datetime.utcnow)
    expires_at = Column(DateTime, nullable=False)  # Auto-release after timeout
    last_heartbeat = Column(DateTime, nullable=False, default=datetime.utcnow)
    
    # Relationships
    task = relationship("Task")
    session = relationship("AgentSession")
    
    def __repr__(self):
        return f"<TaskLock {self.task_id} by {self.session_id} ({self.lock_type})>"
```

### Agent Collaboration Manager

```python
class AgentCollaborationManager:
    """Manages agent check-ins, help requests, and capability matching."""
    
    def __init__(self, db: DatabaseManager):
        self.db = db
        self.capabilities = AGENT_CAPABILITIES
    
    # ===== Check-In/Check-Out =====
    
    def check_in(
        self, 
        agent_name: str, 
        capabilities: Optional[Dict[str, Any]] = None
    ) -> str:
        """
        Register agent session and return session ID.
        
        Args:
            agent_name: Name of the agent (e.g., "GitHub Copilot")
            capabilities: Optional custom capability profile
            
        Returns:
            Session ID for tracking this agent's work
        """
        import uuid
        from datetime import timedelta
        
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
        """Mark agent session as offline."""
        with self.db.get_session() as session:
            agent_session = session.query(AgentSession).filter_by(id=session_id).first()
            if agent_session:
                agent_session.status = "offline"
                agent_session.last_activity = datetime.utcnow()
                session.commit()
                logger.info(f"👋 {agent_session.agent_name} checked out")
    
    def heartbeat(self, session_id: str):
        """Update agent session activity timestamp."""
        with self.db.get_session() as session:
            agent_session = session.query(AgentSession).filter_by(id=session_id).first()
            if agent_session:
                agent_session.last_activity = datetime.utcnow()
                session.commit()
    
    def get_active_agents(self) -> List[Dict[str, Any]]:
        """Get list of currently active agents."""
        with self.db.get_session() as session:
            agents = session.query(AgentSession).filter_by(status="active").all()
            return [{
                "session_id": a.id,
                "agent_name": a.agent_name,
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
        from datetime import timedelta
        
        with self.db.get_session() as session:
            # Check for existing active lock
            existing_lock = session.query(TaskLock).filter_by(
                task_id=task_id
            ).filter(
                TaskLock.lock_type.in_(["active", "soft"])
            ).first()
            
            if existing_lock and existing_lock.session_id != session_id:
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
            session.add(lock)
            
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
        """Release lock on a task."""
        with self.db.get_session() as session:
            lock = session.query(TaskLock).filter_by(
                task_id=task_id,
                session_id=session_id
            ).first()
            
            if lock:
                session.delete(lock)
                
                # Update agent session
                agent_session = session.query(AgentSession).filter_by(
                    id=session_id
                ).first()
                if lock.lock_type == "active":
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
        import uuid
        
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
            requester.help_requests_count += 1
            
            session.commit()
        
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
            
            # Acquire helper lock
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
            
            logger.success(f"🤝 {helper.agent_name} accepted help request from {requester.agent_name}")
            return True
    
    def complete_help_request(self, request_id: str, outcome: str):
        """Mark help request as completed."""
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
        """Get all open help requests."""
        with self.db.get_session() as session:
            requests = session.query(HelpRequest).filter_by(status="open").all()
            return [{
                "id": r.id,
                "task_id": r.task_id,
                "requester": r.requester.agent_name,
                "help_type": r.help_type,
                "context": r.context,
                "urgency": r.urgency,
                "estimated_time": r.estimated_time,
                "created_at": r.created_at.isoformat()
            } for r in requests]
    
    def _broadcast_help_request(self, request_id: str):
        """Broadcast help request to available agents."""
        help_req = None
        with self.db.get_session() as session:
            help_req = session.query(HelpRequest).filter_by(id=request_id).first()
            if not help_req:
                return
            
            print(f"\n🆘 Help Request Broadcast:")
            print(f"  Task: {help_req.task_id}")
            print(f"  Type: {help_req.help_type}")
            print(f"  Urgency: {help_req.urgency}")
            print(f"  Context: {help_req.context}")
            print(f"  Estimated: {help_req.estimated_time}min" if help_req.estimated_time else "")
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
```

## Usage Examples

### Example 1: Agent Check-In
```python
from core.managers import ManagerHub

hub = ManagerHub.create()
collab = hub.collaboration

# Agent checks in at start of session
session_id = collab.check_in("GitHub Copilot")

# Work on tasks...

# Check out when done
collab.check_out(session_id)
```

### Example 2: Requesting Help
```python
# Agent A is stuck on task
session_a = collab.check_in("GitHub Copilot")
collab.acquire_task_lock("AAS-105", session_a, "active")

# Request help after hitting blocker
help_id = collab.request_help(
    task_id="AAS-105",
    requester_session_id=session_a,
    help_type="architecture",
    context="Need advice on gRPC service design patterns",
    urgency="medium",
    estimated_time=20
)

# Agent B sees broadcast and accepts
session_b = collab.check_in("Claude (Sixth)")
collab.accept_help_request(
    request_id=help_id,
    helper_session_id=session_b,
    response_message="Happy to help! I'll review the proto definitions."
)

# Agent B provides guidance (both have access now)
# ...

# Mark help as complete
collab.complete_help_request(help_id, "Suggested repository pattern with streaming")
```

### Example 3: Capability-Based Task Assignment
```python
# System suggests best agent for task
task = hub.tasks.get_task("AAS-110")
best_agent = collab.find_best_agent_for_task(
    task_description=task["description"],
    task_tags=task.get("tags", [])
)

if best_agent:
    print(f"Suggested agent: {best_agent['agent_name']} (match: {best_agent['match_score']:.0%})")
```

### Example 4: Viewing Active Roster
```python
# See who's working
agents = collab.get_active_agents()
for agent in agents:
    print(f"{agent['agent_name']}: {agent['active_tasks']} active tasks")

# See open help requests
help_requests = collab.get_open_help_requests()
for req in help_requests:
    print(f"{req['task_id']}: {req['help_type']} (urgency: {req['urgency']})")
```

## CLI Integration

Add commands to `scripts/aas_cli.py`:

```bash
# Check in
aas collab check-in --agent "GitHub Copilot"

# Check out
aas collab check-out --session <session-id>

# View roster
aas collab roster

# Request help
aas collab help-request AAS-105 \
    --type architecture \
    --context "Need gRPC design review" \
    --urgency medium

# View help requests
aas collab help-list

# Accept help request
aas collab help-accept <help-id> \
    --message "I can help with that"
```

## Conflict Prevention

### Automatic Safeguards
1. **Row-level locks**: SQLite prevents race conditions
2. **Lock expiration**: Auto-release after timeout (default 60min)
3. **Heartbeat monitoring**: Detect stale sessions
4. **Soft locks**: Signal intent before claiming
5. **Read-only helper locks**: Helpers can't modify, only advise

### Best Practices
1. **Always check in**: Signals presence to other agents
2. **Acquire locks before work**: Prevents duplicate effort
3. **Update heartbeat**: Keeps session alive during long tasks
4. **Request help early**: Don't struggle alone for hours
5. **Check roster before claiming**: See if someone more suited is available

## Benefits

### For AI Agents
- **No more conflicts**: Clear ownership and locking
- **Better collaboration**: Easy to request/offer help
- **Optimized assignment**: Matched to strengths
- **Visibility**: See who's working on what

### For Users
- **Faster completion**: Right agent for each task
- **Better quality**: Agents can review each other's work
- **Less rework**: Conflicts prevented upfront
- **Team learning**: Agents share knowledge

### For System
- **Resource efficiency**: No duplicate effort
- **Load balancing**: Distribute based on capacity
- **Audit trail**: Track who did what
- **Metrics**: Measure agent effectiveness

## Implementation Priority

### Phase 1: Core Infrastructure (4 hours)
- ✅ Database models for AgentSession, HelpRequest, TaskLock
- ✅ AgentCollaborationManager implementation
- ✅ Check-in/check-out system
- ✅ Basic locking mechanism

### Phase 2: Help Requests (3 hours)
- ✅ Help request creation and acceptance
- ✅ Broadcasting and notifications
- ✅ Helper lock management
- ✅ Completion tracking

### Phase 3: Capability Matching (3 hours)
- ✅ Capability profile system
- ✅ Task-agent matching algorithm
- ✅ Workload balancing
- ✅ Match scoring

### Phase 4: CLI Integration (2 hours)
- Command implementations
- Interactive prompts
- Status displays
- Help request UX

### Phase 5: Advanced Features (6 hours)
- Session persistence across restarts
- Historical collaboration analytics
- Agent performance scoring
- Team learning insights

## Total Estimated Effort
**18 hours** for full implementation

## Quick Win
**Phase 1-2 (7 hours)** provides immediate value:
- Check-in prevents conflicts
- Help requests enable collaboration
- Clear visibility into who's working

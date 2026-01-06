# AgentCollaborationManager

Manages agent check-ins, help requests, and capability matching.

Key features:
- Check-in/check-out for session tracking
- Task locking to prevent conflicts
- Help request protocol for collaboration
- Capability-based task matching

## Methods

### `accept_help_request(self, request_id: str, helper_session_id: str, response_message: Optional[str] = None) -> bool`

Accept a help request.

Args:
    request_id: Help request to accept
    helper_session_id: Agent offering help
    response_message: Optional message to requester
    
Returns:
    True if accepted successfully

### `acquire_task_lock(self, task_id: str, session_id: str, lock_type: str = 'active', timeout_minutes: int = 60) -> bool`

Acquire lock on a task.

Args:
    task_id: Task to lock
    session_id: Agent session requesting lock
    lock_type: "active" (full control), "soft" (intent), "helper" (read)
    timeout_minutes: Auto-release timeout
    
Returns:
    True if lock acquired, False if task already locked

### `check_in(self, agent_name: str, capabilities: Optional[Dict[str, Any]] = None, agent_version: Optional[str] = None) -> str`

Register agent session and return session ID.

Args:
    agent_name: Name of the agent (e.g., "GitHub Copilot")
    capabilities: Optional custom capability profile
    agent_version: Optional version string
    
Returns:
    Session ID for tracking this agent's work

### `check_out(self, session_id: str)`

Mark agent session as offline.

Args:
    session_id: Session to terminate

### `complete_help_request(self, request_id: str, outcome: str)`

Mark help request as completed.

Args:
    request_id: Help request to complete
    outcome: Summary of outcome

### `find_best_agent_for_task(self, task_description: str, task_tags: Optional[List[str]] = None) -> Optional[Dict[str, Any]]`

Find the best available agent for a task based on capabilities.

Args:
    task_description: Task description text
    task_tags: Optional list of task tags
    
Returns:
    Agent info with match score, or None if no agents available

### `get_active_agents(self) -> List[Dict[str, Any]]`

Get list of currently active agents.

Returns:
    List of agent info dicts

### `get_open_help_requests(self) -> List[Dict[str, Any]]`

Get all open help requests.

Returns:
    List of open help request dicts

### `heartbeat(self, session_id: str)`

Update agent session activity timestamp.

Args:
    session_id: Session to update

### `relay_handoff(self, handoff: core.protocol_manager.HandoffObject)`

Relay handoff context to the target agent or store it for the next claimant.
Implementation for AAS-212.

### `release_task_lock(self, task_id: str, session_id: str)`

Release lock on a task.

Args:
    task_id: Task to unlock
    session_id: Session that owns the lock

### `request_help(self, task_id: str, requester_session_id: str, help_type: str, context: str, urgency: str = 'medium', estimated_time: Optional[int] = None) -> str`

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

# TaskManager

Unified Task Manager combining Handoff, AutoBatch, and Task Tracking.

Responsibilities:
- Task discovery and claiming (FCFS)
- Task status management
- Batch processing orchestration
- Task health monitoring
- Linear synchronization

## Methods

### `add_task(self, priority: str, title: str, description: str, depends_on: str = '-', task_type: str = 'feature') -> str`

Add a new task to the system (DB + Markdown).

### `batch_multiple_tasks(self, max_tasks: int = 10) -> Optional[str]`

Batch multiple unbatched tasks.

### `batch_task(self, task_id: str) -> Optional[str]`

Batch a single task for planning.

### `check_client_timeouts(self, timeout_seconds: int = 90)`

Check for timed-out clients and release their tasks.

### `claim_task(self, task_id: Optional[str] = None, actor_name: str = 'GitHub Copilot') -> Optional[Dict[str, Any]]`

Claim a task (either specific task or next available) using DB locking.

Args:
    task_id: Specific task ID to claim, or None for next available
    actor_name: Name of the actor claiming the task
    
Returns:
    Claimed task dict or None

### `complete_task(self, task_id: str) -> bool`

Mark a task as completed in DB and sync to Markdown.

### `find_next_claimable_task(self, exclude_batched: bool = True) -> Optional[Dict[str, Any]]`

Find the next task that can be claimed according to FCFS rules.

Args:
    exclude_batched: If True, exclude tasks that have been batched
    
Returns:
    Task dict or None

### `find_unbatched_tasks(self, max_count: int = 10) -> List[Dict[str, Any]]`

Find tasks that are eligible for batching but haven't been batched yet.

Criteria:
- Status: queued
- Priority: Medium or Low (High/Urgent handled manually)
- Dependencies: None or all dependencies completed
- Not already batched

Args:
    max_count: Maximum number of tasks to return
    
Returns:
    List of task dicts

### `generate_health_report(self) -> str`

Generate comprehensive health report.

### `get_health_summary(self) -> Dict[str, Any]`

Get comprehensive health summary of all tasks.

### `get_status(self) -> Dict[str, Any]`

Return TaskManager status and metrics.

### `get_task_status(self, task_id: str) -> Dict[str, Any]`

Get comprehensive status for a task including batch processing status.

Returns:
    Dict with task info, status, batch info, etc.

### `register_client(self, client_id: str, hostname: str, client_type: str = 'worker') -> bool`

Register a local client in the database.

### `start_worker(self)`

Start the background task worker.

### `stop_worker(self)`

Stop the background task worker.

### `update_heartbeat(self, client_id: str, cpu_usage: Optional[int] = None, mem_usage: Optional[int] = None) -> bool`

Update a client's heartbeat and metrics.

### `validate(self) -> bool`

Validate TaskManager configuration and state.

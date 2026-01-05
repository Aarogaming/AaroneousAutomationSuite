# SelfHealingManager

Orchestrates automated recovery from environment and UI failures.
Uses KnowledgeManager to find solutions and WorkspaceCoordinator for diagnostics.

## Methods

### `handle_failure(self, error_message: str, task_id: Optional[str] = None) -> Dict[str, Any]`

Attempt to heal a failure.
1. Capture diagnostics.
2. Search knowledge graph for solutions.
3. (Future) Apply automated fix.

### `wrap_execute(self, func, *args, **kwargs)`

Safe execution wrapper that triggers self-healing on failure.

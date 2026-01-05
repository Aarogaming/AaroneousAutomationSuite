# BatchManager

Unified manager for OpenAI Batch API operations.

## Methods

### `batch_multiple_tasks(self, tasks: List[Dict[str, Any]]) -> Optional[str]`

High-level method to batch multiple tasks.

### `batch_task(self, task_id: str, task_details: Dict[str, Any]) -> Optional[str]`

High-level method to batch a single task.

### `get_batch_status(self, batch_id: str) -> Dict[str, Any]`

Get batch status and progress.

### `get_status(self) -> dict`

Return BatchManager status.

### `list_active_batches(self) -> List[Dict[str, Any]]`

List all active/pending batches.

### `submit_batch(self, requests: List[Dict[str, Any]], description: str, metadata: Optional[Dict[str, Any]] = None) -> str`

Submit a batch job with automatic request formatting.

### `validate(self) -> bool`

Validate BatchManager state.

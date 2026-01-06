# KnowledgeManager

Manager for the Multi-Modal Knowledge Graph.
Handles indexing, searching, and relationship mapping.

## Methods

### `add_error_pattern(self, error_message: str, solution: Optional[str] = None, task_id: Optional[str] = None)`

Index a new error pattern and its solution.

### `find_solutions(self, query: str, limit: int = 5) -> List[Dict[str, Any]]`

Search for solutions to a given error/query.

### `index_task_result(self, task_id: str, success: bool, output: str)`

Automatically index the result of a completed task.

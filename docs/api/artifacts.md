# ArtifactManager

Manages the lifecycle and storage of AAS artifacts.

Features:
- Task-specific artifact directory management
- Build output organization
- Report generation and storage
- Multi-client path resolution

## Methods

### `cleanup_old_artifacts(self, days: int = 30)`

Remove artifacts older than specified days (placeholder for future).

### `create_task_readme(self, task_id: str, title: str, assignee: str)`

Initialize a README.md for a new task artifact.

### `get_build_path(self, build_name: str) -> pathlib.Path`

Get path for a build output.

### `get_status(self) -> dict`

Return ArtifactManager status.

### `get_task_dir(self, task_id: str) -> pathlib.Path`

Get the artifact directory for a specific task.

### `store_report(self, name: str, content: str, sub_dir: str = 'reports') -> pathlib.Path`

Store a generated report.

### `validate(self) -> bool`

Validate ArtifactManager state.

# WorkspaceCoordinator

Manages workspace file-system hygiene and organization.

Features:
- Duplicate file detection (by content hash)
- Large file identification
- Temporary file cleanup
- Runaway bot detection
- Workspace health reporting

## Methods

### `capture_diagnostic_pack(self, task_id: Optional[str] = None) -> str`

Capture a diagnostic pack for self-healing analysis.
Includes workspace report, recent logs, and environment info.

### `check_git_compatibility(self) -> Dict[str, Any]`

Check if workspace files are git-repo size-friendly.
Target: All files < 50MB.

### `cleanup_duplicates(self, dry_run: bool = True, keep_strategy: str = 'newest') -> List[pathlib.Path]`

Remove duplicate files, keeping one copy.

Args:
    dry_run: If True, only report what would be deleted
    keep_strategy: "newest", "oldest", or "shortest_path"
    
Returns:
    List of files that were (or would be) deleted

### `cleanup_temp_files(self, dry_run: bool = True, age_days: int = 7) -> List[pathlib.Path]`

Remove temporary files older than specified age.

Args:
    dry_run: If True, only report what would be deleted
    age_days: Delete files older than this many days
    
Returns:
    List of files that were (or would be) deleted

### `defrag_workspace(self, dry_run: bool = True) -> List[str]`

Ported logic from defrag_workspace.ps1.
Consolidates build outputs, UI audits, and documentation.

### `detect_runaway_bot(self, time_window_minutes: int = 5) -> Dict[str, Any]`

Detect signs of runaway bot activity.

Checks for:
- Excessive file creation in short time
- Large number of duplicate files
- Unusual file patterns

Args:
    time_window_minutes: Time window for recent file check
    
Returns:
    Dict with detection results and metrics

### `find_duplicates(self, scan_dirs: Optional[List[str]] = None) -> Dict[str, List[pathlib.Path]]`

Find duplicate files by content hash.

Args:
    scan_dirs: Specific directories to scan, or None for all
    
Returns:
    Dict mapping hash -> list of file paths with that hash

### `find_large_files(self, min_size_mb: float = 10) -> List[Tuple[pathlib.Path, float]]`

Find files larger than specified size.

Args:
    min_size_mb: Minimum file size in MB
    
Returns:
    List of (path, size_mb) tuples

### `find_temp_files(self) -> List[pathlib.Path]`

Find temporary files based on naming patterns.

### `generate_workspace_report(self) -> Dict[str, Any]`

Generate comprehensive workspace health report.

Returns:
    Dict with workspace metrics and issues

### `get_status(self) -> dict`

Return WorkspaceCoordinator status.

### `save_report(self, report: Dict, output_path: str = 'artifacts/workspace_health.json')`

Save workspace report to file.

### `validate(self) -> bool`

Validate WorkspaceCoordinator state.

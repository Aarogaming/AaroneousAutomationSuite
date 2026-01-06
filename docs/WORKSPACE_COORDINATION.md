# Workspace Coordination Guide

The unified Task Manager now includes **Workspace Coordination** capabilities to maintain a clean, organized, and efficient workspace.

## Features

### 1. Duplicate File Detection
Identifies files with identical content using SHA256 hashing.

```bash
# Scan for duplicates
python scripts/task_manager_cli.py workspace-duplicates
```

**Output:**
- Number of duplicate sets found
- List of duplicate file paths
- File sizes and total wasted space
- Calculated storage waste

### 2. Large File Identification
Finds files exceeding a specified size threshold (default: 10MB).

```bash
# Scan for large files
python scripts/task_manager_cli.py workspace-scan
```

**Tracks:**
- Files over 10MB
- Total count and sizes
- File locations

### 3. Temporary File Cleanup
Detects and removes temporary files based on naming patterns:
- `temp_*`, `tmp_*`
- `.tmp`, `.bak`
- Files ending with `~`

```bash
# Clean up temp files (dry run)
python scripts/task_manager_cli.py workspace-cleanup --dry-run

# Actually delete files
python scripts/task_manager_cli.py workspace-cleanup
```

### 4. Runaway Bot Detection
Monitors for excessive file creation that might indicate a runaway process.

**Detection Criteria:**
- More than 50 files/minute
- More than 10 duplicate files created recently
- More than 100 files in a single directory

```bash
# Check for runaway activity
python scripts/task_manager_cli.py detect-runaway
```

**Response:**
- Alerts if thresholds exceeded
- Shows file creation rate
- Identifies problematic directories
- Tracks recent duplicate creation

### 5. Workspace Health Reports
Generates comprehensive reports with all metrics.

```bash
# Generate full health report
python scripts/task_manager_cli.py workspace-report
```

**Report Contents:**
- Duplicate file analysis
- Large file inventory
- Temp file statistics
- Runaway bot check results
- Overall health score (Excellent/Good/Fair/Needs Attention)
- Saved to `artifacts/workspace_health.json`

## Python API

```python
from core.handoff.task_manager import TaskManager
from core.config import AASConfig

# Initialize
config = AASConfig()
tm = TaskManager(config)

# Scan for duplicates
duplicates = tm.scan_workspace_duplicates()
# Returns: Dict[hash -> List[Path]]

# Find large files
large_files = tm.scan_large_files(min_size_mb=10)
# Returns: List[(Path, size_mb)]

# Check for runaway bot
runaway = tm.detect_runaway_bot()
# Returns: Dict with detection results

# Cleanup workspace
results = tm.cleanup_workspace(
    dry_run=True,  # Set False to actually delete
    cleanup_duplicates=True,
    cleanup_temps=True
)

# Generate health report
report = tm.generate_workspace_report()
tm.save_workspace_report("artifacts/workspace_health.json")
```

## Workspace Coordinator Configuration

The `WorkspaceCoordinator` can be customized:

```python
from core.handoff.workspace_coordinator import WorkspaceCoordinator

coordinator = WorkspaceCoordinator(workspace_root=".")

# Customize ignore patterns
coordinator.ignore_dirs.add("custom_ignore_folder")
coordinator.ignore_extensions.add(".custom")

# Adjust runaway thresholds
coordinator.max_files_per_minute = 100  # More lenient
coordinator.max_duplicates_threshold = 20
coordinator.max_file_size_mb = 50
```

## Automated Workflows

### Daily Cleanup Routine
```bash
# 1. Check health
python scripts/task_manager_cli.py workspace-scan

# 2. Review duplicates
python scripts/task_manager_cli.py workspace-duplicates

# 3. Cleanup (dry run first)
python scripts/task_manager_cli.py workspace-cleanup --dry-run

# 4. If satisfied, run actual cleanup
python scripts/task_manager_cli.py workspace-cleanup

# 5. Generate report
python scripts/task_manager_cli.py workspace-report
```

### Integration with Task Lifecycle

The workspace coordinator integrates with the task management system:

```python
# Example: Check workspace health before claiming tasks
tm = TaskManager(config)

# Get combined health
report = tm.generate_workspace_report()

if report["health_score"] in ["Excellent", "Good"]:
    # Workspace is clean, proceed with task
    task = tm.find_next_claimable_task()
    tm.claim_task(task_id=task["id"])
else:
    # Clean up first
    print("Workspace needs attention!")
    tm.cleanup_workspace(dry_run=False)
```

## Best Practices

1. **Run workspace scans regularly** - Daily or before major tasks
2. **Always use dry-run first** - Review what will be deleted
3. **Monitor runaway detection** - Catches issues early
4. **Keep health reports** - Track workspace trends over time
5. **Customize thresholds** - Adjust based on your workflow

## Ignored Directories

By default, these directories are excluded from scans:
- `.git`, `.venv`, `venv`, `env`
- `__pycache__`, `.pytest_cache`, `.mypy_cache`
- `node_modules`
- `build`, `dist`, `*.egg-info`

## Health Score Calculation

The health score is based on:
- **Duplicate waste** (MB)
- **Temp file waste** (MB)
- **Runaway bot activity**

**Scoring:**
- **Excellent**: No issues detected
- **Good**: Minor issues (1-2 points)
- **Fair**: Some issues (3-4 points)
- **Needs Attention**: Major issues (5+ points)

## Troubleshooting

### "Permission denied" errors
- Some files may be locked by other processes
- Run with elevated permissions if needed
- Use `--dry-run` to identify problematic files first

### False positive duplicates
- Legitimate backup files may be flagged
- Review the list before cleanup
- Adjust ignore patterns if needed

### Runaway detection triggered incorrectly
- Adjust `max_files_per_minute` threshold
- Increase `time_window_minutes` for averaging
- Add specific directories to ignore list

## Future Enhancements

Planned features:
- [ ] Automatic cleanup scheduling
- [ ] Email/Slack alerts for runaway detection
- [ ] Integration with Linear task creation for cleanup tasks
- [ ] Configurable cleanup policies per directory
- [ ] File pattern-based retention policies
- [ ] Disk usage trending and forecasting

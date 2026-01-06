# Unified Task Manager - Quick Reference

## Overview
The unified Task Manager consolidates Handoff, AutoBatch, and task tracking into a single system.

## Quick Start

```bash
# Activate environment
.\.venv\Scripts\Activate.ps1

# List all tasks
python scripts/aas_cli.py task list

# Claim next available task
python scripts/aas_cli.py task claim

# Claim a specific task
python scripts/aas_cli.py task claim AAS-XXX

# Check task status
python scripts/aas_cli.py task status AAS-XXX

# View system health
python scripts/aas_cli.py health

# Workspace Scan
python scripts/aas_cli.py workspace scan

# Workspace Defragmentation (Consolidate structure)
python scripts/aas_cli.py workspace defrag

# Start Client Heartbeat (Multi-client support)
python scripts/aas_cli.py client heartbeat

# Batch a task
python scripts/aas_cli.py batch submit AAS-XXX
```

## Python API

```python
from core.handoff.task_manager import TaskManager
from core.config import AASConfig

# Initialize
tm = TaskManager(AASConfig())

# Task Discovery
unbatched = tm.find_unbatched_tasks(max_count=10)
next_task = tm.find_next_claimable_task()

# Task Operations
claimed = tm.claim_task(task_id="AAS-XXX", actor_name="Agent Name")
status = tm.get_task_status("AAS-XXX")
completed = tm.complete_task("AAS-XXX")

# Batch Processing
batch_id = await tm.batch_task("AAS-XXX")
multi_batch = await tm.batch_multiple_tasks(task_ids=["AAS-XXX", "AAS-YYY"])

# Health & Analytics
health = tm.get_health_summary()
report_path = tm.generate_health_report()
```

## Key Features

### Unified Interface
- Single point of access for all task operations
- Consistent API across all functions
- Database-backed state with Markdown synchronization
- Atomic task claiming with row-level locking

### Multi-Client Support
- Client registration and heartbeat monitoring
- Automatic task release on client timeout
- Shared artifact management via `ArtifactManager`

### Batch Tracking
- Tracks which tasks have been batched
- Prevents duplicate batch submissions
- Links tasks to batch IDs
- Persists history to `artifacts/batch/history.json`

### Smart Discovery
- Finds unbatched tasks automatically
- Respects task dependencies
- Filters by priority and status
- FCFS claiming with priority sorting

### Health Monitoring
- Task board health checks
- Stale task detection (>3 days in progress)
- Unassigned high-priority alerts
- Batch processing statistics

## Files

### Core
- `core/handoff/task_manager.py` - Main TaskManager class
- `core/handoff/manager.py` - HandoffManager (underlying)
- `core/batch/processor.py` - BatchProcessor (underlying)

### CLI
- `scripts/task_manager_cli.py` - Command-line interface

### Data
- `handoff/ACTIVE_TASKS.md` - Task board source of truth
- `artifacts/batch/history.json` - Batch tracking
- `artifacts/handoff/AAS-XXX/` - Task artifacts

## Workflow

1. **Find Tasks**: `list-unbatched` or `find-next`
2. **Claim Task**: `claim AAS-XXX`
3. **Work on It**: Implement the task
4. **Optional Batch**: `batch AAS-XXX` for AI planning
5. **Monitor**: `health` for overall status
6. **Complete**: Mark as done when finished

## Tips

- Use `find-next` to get the highest priority claimable task
- Use `list-unbatched` to see what can be batched
- Check `health` regularly for task board status
- Batch multiple tasks at once with `batch-all`
- Use `status` before starting work on a task

## Integration

The Task Manager integrates with:
- **Linear API**: Two-way sync of tasks
- **OpenAI Batch API**: Bulk processing
- **Handoff System**: Task claiming and status
- **Health Monitoring**: System-wide health checks

## Benefits

- ✅ Single unified interface
- ✅ Batch tracking prevents duplicates
- ✅ Smart task discovery
- ✅ Automated workflow
- ✅ Health monitoring
- ✅ Clean CLI and Python API

## Support

For issues or questions:
- Check task board: `handoff/ACTIVE_TASKS.md`
- View health: `python scripts/task_manager_cli.py health`
- Check logs in terminal output
- Review implementation: `artifacts/handoff/AAS-113/README.md`

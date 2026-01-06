# Batch Result Recycling & Auto-Clear System

## Overview

The batch recycling system automates the full lifecycle of OpenAI batch processing:

1. **Auto-Clear**: Monitors active batches, retrieves completed results, archives old files
2. **Recycler**: Extracts actionable tasks from batch results and adds them to task board
3. **Orchestrator**: Combines both for hands-free automation

## Architecture

```
┌─────────────────────────────────────────────────────────────┐
│                   Batch Workflow Lifecycle                   │
└─────────────────────────────────────────────────────────────┘
                            │
                            ▼
┌─────────────────────────────────────────────────────────────┐
│ STEP 1: Auto-Clear Batch Backlog                            │
│ ────────────────────────────────────────────────────────────│
│ • Check all active batches via OpenAI API                   │
│ • Retrieve completed batch results (output files)           │
│ • Update monitor_state.json                                 │
│ • Move to completed_batches array                           │
│ • Archive results older than 30 days                        │
└─────────────────────────────────────────────────────────────┘
                            │
                            ▼
┌─────────────────────────────────────────────────────────────┐
│ STEP 2: Recycle Results into Task List                      │
│ ────────────────────────────────────────────────────────────│
│ • Parse batch result files (JSON)                           │
│ • Extract actionable items using patterns:                  │
│   - Numbered implementation steps                           │
│   - TODO/FIXME/ACTION items                                 │
│   - "Requires implementation" sections                      │
│ • Create tasks via TaskManager.add_task()                   │
│ • Link tasks to original parent task (dependencies)         │
│ • Log processed batches to avoid duplicates                 │
└─────────────────────────────────────────────────────────────┘
                            │
                            ▼
┌─────────────────────────────────────────────────────────────┐
│ STEP 3: Generate Reports & Cleanup                          │
│ ────────────────────────────────────────────────────────────│
│ • Show statistics (tasks created, batches completed)        │
│ • Evaluate criteria (completion rate, old batches)          │
│ • Archive old results to artifacts/batch/archive/           │
│ • Update recycled_batches.json log                          │
└─────────────────────────────────────────────────────────────┘
```

## Components

### 1. Batch Auto-Clear (`scripts/batch_auto_clear.py`)

Automatically clears batch backlog based on configurable criteria.

**Criteria:**
```python
{
    "max_pending_age_hours": 24,      # Auto-retrieve batches older than 24h
    "max_active_batches": 10,         # Trigger cleanup if > 10 active
    "min_completion_rate": 0.5,       # At least 50% should be complete
    "auto_retrieve_completed": True,  # Auto-retrieve completed batches
    "archive_old_results": True,      # Archive results > 30 days
    "archive_age_days": 30
}
```

**Usage:**
```bash
# Dry run (preview)
python scripts/batch_auto_clear.py --dry-run

# Live run
python scripts/batch_auto_clear.py

# Just show report
python scripts/batch_auto_clear.py --report
```

**Output:**
```
📊 BATCH BACKLOG AUTO-CLEAR REPORT
====================================
Statistics:
  ✓ Batches checked: 3
  ✓ Newly completed: 1
  ✓ Results retrieved: 1
  ✗ Failed batches: 0
  📦 Results archived: 2

Criteria Status:
  ✓ max_active_batches: PASS
  ✓ completion_rate: PASS
  ✓ no_old_pending: PASS
```

### 2. Batch Recycler (`scripts/batch_recycler.py`)

Extracts actionable items from batch results and creates tasks.

**Pattern Matching:**

1. **Implementation Steps** - Numbered/phased steps
   ```
   Step 1: Setup database schema
   Step 2: Create API endpoints
   ...
   ```
   → Creates tasks: "Implement: Setup database schema"

2. **TODO Items** - Explicit action markers
   ```
   TODO: Add error handling for edge cases
   FIXME: Optimize query performance
   ```
   → Creates tasks: "TODO: Add error handling..."

3. **Required Implementation** - Sections marked for implementation
   ```
   Requires implementation: Authentication middleware with JWT validation
   ```
   → Creates tasks: "Required: Authentication middleware..."

**Usage:**
```bash
# Dry run (show what would be created)
python scripts/batch_recycler.py --dry-run

# Process all pending batches
python scripts/batch_recycler.py

# Process specific file
python scripts/batch_recycler.py --file artifacts/batch/results/batch_XXX_processed.json

# Reprocess already-processed batches
python scripts/batch_recycler.py --force
```

**Output:**
```
📊 Recycling Summary:
  Batches processed: 3
  Tasks created: 12
  Skipped: 2
  Errors: 0
```

### 3. Batch Workflow Orchestrator (`scripts/batch_workflow.py`)

Combines auto-clear + recycler for full automation.

**Usage:**
```bash
# Dry run (preview entire workflow)
python scripts/batch_workflow.py --dry-run

# Live run
python scripts/batch_workflow.py
```

**Output:**
```
🚀 Starting Batch Workflow Orchestrator...
Mode: LIVE

============================================================
STEP 1: Auto-Clear Batch Backlog
============================================================
📊 BATCH BACKLOG AUTO-CLEAR REPORT
...

============================================================
STEP 2: Recycle Results into Task List
============================================================
📋 Recycling Summary:
  Batches processed: 1
  Tasks created: 5
  Skipped: 2
  Errors: 0

============================================================
🎉 WORKFLOW COMPLETE
============================================================
Duration: 12.34s
Mode: LIVE

Summary:
  ✓ Batches completed: 1
  ✓ Results retrieved: 1
  ✓ Tasks created: 5
  ✓ Files archived: 2
```

## File Structure

```
artifacts/batch/
├── monitor_state.json              # Tracks active/completed batches
├── recycled_batches.json           # Log of processed batches
├── results/
│   ├── batch_XXX_processed.json    # Retrieved batch results
│   └── batch_YYY_processed.json
└── archive/
    └── batch_ZZZ_processed.json    # Archived old results (>30 days)
```

## Automation

### Option 1: Windows Task Scheduler

1. Open Task Scheduler
2. Create Basic Task → "Batch Workflow Automation"
3. Trigger: Daily at 2:00 AM
4. Action: Start a program
   - Program: `C:\Users\...\AaroneousAutomationSuite\.venv\Scripts\python.exe`
   - Arguments: `scripts/batch_workflow.py`
   - Start in: `C:\Users\...\AaroneousAutomationSuite`

### Option 2: Cron (Linux/macOS)

```bash
# Edit crontab
crontab -e

# Add line (runs daily at 2 AM)
0 2 * * * cd /path/to/AaroneousAutomationSuite && .venv/bin/python scripts/batch_workflow.py

# Verify
crontab -l
```

### Option 3: AAS Service Integration

Add to `core/main.py` as background task:

```python
import asyncio
from scripts.batch_workflow import BatchWorkflowOrchestrator

async def batch_workflow_loop():
    """Background task for batch processing"""
    orchestrator = BatchWorkflowOrchestrator()
    
    while True:
        try:
            orchestrator.run_full_workflow(dry_run=False)
        except Exception as e:
            logger.error(f"Batch workflow failed: {e}")
        
        # Run every 6 hours
        await asyncio.sleep(6 * 60 * 60)

# In main()
asyncio.create_task(batch_workflow_loop())
```

## Configuration

### Customize Auto-Clear Criteria

Edit `scripts/batch_auto_clear.py`:

```python
self.criteria = {
    "max_pending_age_hours": 24,      # Your threshold
    "max_active_batches": 10,         # Your limit
    "min_completion_rate": 0.5,       # Your rate
    "auto_retrieve_completed": True,  # Enable/disable
    "archive_old_results": True,      # Enable/disable
    "archive_age_days": 30            # Your age threshold
}
```

### Customize Pattern Matching

Edit `scripts/batch_recycler.py` → `extract_actionable_items()`:

```python
# Add custom pattern
custom_pattern = r'YOUR_REGEX_PATTERN'
matches = re.finditer(custom_pattern, content)
# ... create tasks from matches
```

## Example: Full Workflow

```bash
# 1. Initial setup (one-time)
cd AaroneousAutomationSuite

# 2. Test with dry run
python scripts/batch_workflow.py --dry-run

# 3. Review what would happen
# Check output for tasks that would be created

# 4. Run live
python scripts/batch_workflow.py

# 5. Verify results
python scripts/task_manager_cli.py status

# 6. Schedule for automation (Windows)
# Use Task Scheduler as described above

# 7. Monitor logs
tail -f artifacts/batch/recycled_batches.json
```

## Troubleshooting

### No actionable items extracted

**Problem:** Recycler finds no tasks in batch results

**Solution:**
1. Check batch result content: `cat artifacts/batch/results/batch_XXX_processed.json`
2. Verify patterns match your content
3. Add custom patterns in `extract_actionable_items()`

### Tasks already exist

**Problem:** Duplicate tasks created

**Solution:**
1. Recycler automatically skips processed batches
2. Check `artifacts/batch/recycled_batches.json`
3. Use `--force` flag only if intentional reprocessing

### Batch not completing

**Problem:** Active batches stuck for > 24 hours

**Solution:**
1. Check OpenAI status: https://status.openai.com
2. Verify batch status manually: `python scripts/check_batch_status.py`
3. Auto-clear will flag batches > 24h old

### Archive not working

**Problem:** Old results not archived

**Solution:**
1. Check criteria: `archive_old_results = True`
2. Verify age threshold: `archive_age_days = 30`
3. Ensure `artifacts/batch/archive/` directory exists

## Integration with Task Manager

Recycled tasks automatically:
- ✓ Appear in `handoff/ACTIVE_TASKS.md`
- ✓ Stored in SQLite database (`artifacts/aas.db`)
- ✓ Linked to parent task (via dependencies)
- ✓ Set to "queued" status
- ✓ Priority: "medium" by default
- ✓ Ready for FCFS claiming by agents

**Verify integration:**
```bash
# List all tasks
python scripts/task_manager_cli.py list

# Show specific task
python scripts/task_manager_cli.py show AAS-XXX

# Claim task
python scripts/task_manager_cli.py claim AAS-XXX --agent "YourAgent"
```

## Cost Savings

With automatic batch processing:
- ✅ 50% cost reduction (batch API vs real-time)
- ✅ Background processing (no blocking)
- ✅ Auto-recycling (no manual intervention)
- ✅ Smart archiving (disk space management)

**Example savings from actual usage:**
```
Batches completed: 3
Tasks processed: 14
Total cost saved: $24.35
```

## Best Practices

1. **Always dry-run first** - Preview changes before executing
2. **Schedule off-hours** - Run workflow during low-activity periods
3. **Monitor logs** - Check `recycled_batches.json` regularly
4. **Review created tasks** - Validate quality of extracted items
5. **Customize patterns** - Adapt to your batch result format
6. **Archive regularly** - Keep results directory clean
7. **Test criteria** - Adjust thresholds based on your workflow

## Next Steps

1. Test with existing batch results:
   ```bash
   python scripts/batch_workflow.py --dry-run
   ```

2. Configure automation (Task Scheduler/cron)

3. Customize pattern matching for your use case

4. Integrate with existing task management workflows

5. Monitor and adjust criteria based on results

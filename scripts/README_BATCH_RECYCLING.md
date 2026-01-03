# Batch Recycling System - Quick Start

## What It Does

Automatically converts completed batch results back into actionable tasks on your task board.

**Flow:**
```
Batch Completes → Extract Steps → Create Tasks → Auto-Clear Backlog
```

## Quick Commands

```bash
# Preview what would happen (dry run)
python scripts/batch_workflow.py --dry-run

# Run it live
python scripts/batch_workflow.py

# Just check status
python scripts/batch_auto_clear.py --report

# Verify created tasks
python scripts/verify_recycled_tasks.py
```

## What Just Happened

✅ **AAS-113** batch result analyzed  
✅ **5 tasks** extracted and created:
- AAS-114: Step 1: Project Setup
- AAS-115: Step 2: Backend Implementation  
- AAS-116: Step 3: Frontend Development
- AAS-117: Step 4: Integration
- AAS-118: Step 5: Monitoring and Alerts

All tasks:
- **Depend on AAS-113** (original parent)
- **Status: queued** (ready for claiming)
- **Priority: medium**
- Stored in database + task board

## Automation Options

### Windows Task Scheduler
Run daily at 2 AM:
```
Program: .venv\Scripts\python.exe
Arguments: scripts\batch_workflow.py
Start in: C:\Users\...\AaroneousAutomationSuite
```

### Cron (Linux/macOS)
```bash
0 2 * * * cd /path/to/AAS && .venv/bin/python scripts/batch_workflow.py
```

### AAS Service Integration
Add to `core/main.py`:
```python
asyncio.create_task(batch_workflow_loop())  # Runs every 6 hours
```

## How It Works

1. **Auto-Clear** checks OpenAI API for completed batches
2. **Retrieves** result files from completed batches
3. **Extracts** actionable items using pattern matching:
   - `**Step N: Title**` → Implementation tasks
   - `TODO:` / `FIXME:` → High-priority todos
   - `Requires implementation:` → Required features
4. **Creates** tasks via TaskManager with dependencies
5. **Archives** old results (>30 days)
6. **Logs** everything to avoid duplicates

## Pattern Matching

The recycler looks for:
- ✅ **Step X:** format (like from AAS-113)
- ✅ TODO/FIXME/ACTION markers
- ✅ "Requires implementation" sections
- ✅ Major section headers (### N. Title)

## Files

- `scripts/batch_workflow.py` - Main orchestrator
- `scripts/batch_auto_clear.py` - Check & retrieve batches
- `scripts/batch_recycler.py` - Extract & create tasks
- `artifacts/batch/recycled_batches.json` - Processed log
- `artifacts/batch/results/` - Retrieved batch files

## Configuration

Edit criteria in `batch_auto_clear.py`:
```python
self.criteria = {
    "max_pending_age_hours": 24,
    "max_active_batches": 10,
    "min_completion_rate": 0.5,
    "auto_retrieve_completed": True,
    "archive_old_results": True,
    "archive_age_days": 30
}
```

## Troubleshooting

**No items extracted?**
- Check result file content
- Adjust patterns in `batch_recycler.py`

**Duplicate tasks?**
- Recycler auto-skips processed batches
- Check `recycled_batches.json` log

**Old batches stuck?**
- Check OpenAI status page
- Run `--report` to see backlog status

## Cost Savings

- Batch API: **50% cheaper** than real-time
- **$24.35 saved** so far (14 tasks across 3 batches)
- Fully automated background processing

## Full Documentation

See [BATCH_RECYCLING.md](../docs/BATCH_RECYCLING.md) for complete guide.

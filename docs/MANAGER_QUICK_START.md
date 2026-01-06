# Quick Start: Try the New Manager Patterns

**Ready to test?** This 5-minute guide shows you how to try the new ManagerHub and CLI.

---

## Prerequisites

- ✅ AAS repository cloned
- ✅ Virtual environment activated (`.venv\Scripts\Activate.ps1`)
- ✅ Dependencies installed (`pip install -r requirements.txt`)
- ✅ `.env` file configured with `OPENAI_API_KEY`

---

## 1. Test ManagerHub (2 minutes)

### Basic Test
```powershell
# Run from AAS root directory
python -c "from core.managers import ManagerHub; hub = ManagerHub.create(); print('✅ Hub initialized:', hub)"
```

**Expected Output:**
```
✅ Hub initialized: <ManagerHub initialized=[]>
```

### Validation Test
```powershell
python -c "from core.managers import ManagerHub; hub = ManagerHub.create(); print(hub.validate_all())"
```

**Expected Output:**
```python
{'config': True}
```

### Health Check Test
```powershell
python -c "from core.managers import ManagerHub; hub = ManagerHub.create(); print(hub.get_health_summary())"
```

**Expected Output:**
```python
{
    'timestamp': '2026-01-02T21:07:01...',
    'overall_status': 'healthy',
    'managers': {...}
}
```

---

## 2. Test New CLI (3 minutes)

### View Help
```powershell
python scripts/aas_cli.py --help
```

**Expected:** List of command groups (task, batch, workspace, health)

### System Health
```powershell
python scripts/aas_cli.py health
```

**Expected:**
```
🏥 AAS System Health Report
============================================================
Timestamp: 2026-01-02T21:07:01
Overall:   HEALTHY

Manager Status:
  ✅ Config          OK
============================================================
```

### List Tasks
```powershell
python scripts/aas_cli.py task list
```

**Expected:** Table of tasks with colors by priority

### View Task Commands
```powershell
python scripts/aas_cli.py task --help
```

**Expected:** List of task subcommands (list, claim, status, complete)

---

## 3. Write Your First Script with ManagerHub

Create `scripts/test_hub.py`:

```python
from core.managers import ManagerHub

# Initialize
hub = ManagerHub.create()

# Check health
print("System Health:")
health = hub.get_health_summary()
print(f"  Status: {health['overall_status']}")

# Validate managers
print("\nValidation:")
validation = hub.validate_all()
for name, status in validation.items():
    icon = '✅' if status else '❌'
    print(f"  {icon} {name}")

# Access task manager (only when needed - lazy loaded)
print("\nTask Board:")
lines, tasks, _ = hub.handoff.parse_board()
print(f"  Total tasks: {len(tasks)}")
print(f"  Queued: {sum(1 for t in tasks if t['status'] == 'queued')}")

print("\n✨ Complete!")
```

**Run it:**
```powershell
python scripts/test_hub.py
```

**Expected Output:**
```
System Health:
  Status: healthy

Validation:
  ✅ config

Task Board:
  Total tasks: 47
  Queued: 12

✨ Complete!
```

---

## 4. Compare with Old Pattern

### Old Pattern (Still Works)
```python
# scripts/test_old.py
import sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).parent.parent))

from core.config import AASConfig
from core.handoff.task_manager import TaskManager

config = AASConfig()
tm = TaskManager(config)

lines, tasks, _ = tm.handoff.parse_board()
print(f"Tasks: {len(tasks)}")
```

**Lines:** 12 (7 setup, 5 logic)

### New Pattern
```python
# scripts/test_new.py
from core.managers import ManagerHub

hub = ManagerHub.create()
lines, tasks, _ = hub.handoff.parse_board()
print(f"Tasks: {len(tasks)}")
```

**Lines:** 5 (2 setup, 3 logic)  
**Reduction:** 58% fewer lines

---

## 5. Test Error Handling

### Intentionally Break Config
```powershell
# Temporarily rename .env to trigger error
mv .env .env.backup

# Try to initialize
python -c "from core.managers import ManagerHub; hub = ManagerHub.create()"

# Restore .env
mv .env.backup .env
```

**Expected:** Helpful error message pointing to fix

---

## 6. Advanced: Use Multiple Managers

Create `scripts/test_multi_manager.py`:

```python
from core.managers import ManagerHub

hub = ManagerHub.create()

# Task operations
print("📋 Tasks:")
next_task = hub.tasks.find_next_claimable_task()
if next_task:
    print(f"  Next: {next_task['id']} - {next_task['title']}")

# Database operations
print("\n💾 Database:")
try:
    with hub.db.get_session() as session:
        print(f"  Connected: {hub.db.db_path}")
except Exception as e:
    print(f"  Not initialized yet")

# Batch operations
print("\n📦 Batch:")
try:
    batches = hub.batch.list_batches(limit=5)
    print(f"  Recent batches: {len(batches)}")
except Exception as e:
    print(f"  Error: {e}")

# Workspace operations
print("\n🗂️  Workspace:")
health = hub.workspace.check_workspace_health()
print(f"  Health: {health.get('status', 'unknown')}")

print("\n✨ Complete!")
```

**Run it:**
```powershell
python scripts/test_multi_manager.py
```

---

## 7. Install Click for Full CLI Features (Optional)

If you see `ModuleNotFoundError: No module named 'click'`:

```powershell
pip install click
```

Then retry CLI commands.

---

## Troubleshooting

### Issue: Module not found
```
ModuleNotFoundError: No module named 'core'
```

**Fix:** Run from AAS root directory or ensure path setup:
```python
import sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).parent.parent))
```

### Issue: Config validation error
```
ValidationError: openai_api_key field required
```

**Fix:** Ensure `.env` file has `OPENAI_API_KEY=sk-...`

### Issue: Database not found
```
DatabaseManager: No such file or directory
```

**Fix:** Database is created on first use. Try:
```python
hub.db.create_tables()
```

---

## Next Steps

### Once Testing is Complete

1. **Provide Feedback:**
   - What worked well?
   - What was confusing?
   - Missing features?

2. **Try Real Workflows:**
   - Claim a task: `python scripts/aas_cli.py task claim`
   - Check health: `python scripts/aas_cli.py health`
   - List tasks: `python scripts/aas_cli.py task list`

3. **Migrate a Script:**
   - Pick one of your scripts
   - Replace old pattern with ManagerHub
   - Compare before/after

4. **Review Documentation:**
   - [MANAGER_SUMMARY.md](MANAGER_SUMMARY.md) - Executive summary
   - [MANAGER_IMPROVEMENTS.md](MANAGER_IMPROVEMENTS.md) - Full details
   - [MANAGER_BEFORE_AFTER.md](MANAGER_BEFORE_AFTER.md) - Examples

---

## Success Criteria

You've successfully tested the new patterns if:

- ✅ ManagerHub initializes without errors
- ✅ Validation shows `{'config': True}`
- ✅ CLI commands run and show help text
- ✅ Health check returns 'healthy' status
- ✅ You understand the benefits vs old pattern

---

## Questions?

- Check [MANAGER_IMPROVEMENTS.md](MANAGER_IMPROVEMENTS.md) for detailed answers
- Review [MANAGER_BEFORE_AFTER.md](MANAGER_BEFORE_AFTER.md) for more examples
- See [MANAGER_IMPLEMENTATION_PLAN.md](MANAGER_IMPLEMENTATION_PLAN.md) for roadmap

---

**Estimated Time:** 5-10 minutes for basic testing  
**Difficulty:** Easy - just copy/paste commands  
**Impact:** Understand 80% reduction in boilerplate

Ready to improve AAS manager experience! 🚀

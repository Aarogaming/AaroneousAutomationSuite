# Before & After: Manager Usage Examples

This document shows real-world examples of how manager improvements simplify AAS usage.

---

## Example 1: Simple Task Claiming Script

### ❌ Before (Current Pattern)

```python
# File: scripts/my_task_script.py
import sys
from pathlib import Path

# Add parent directory to path
sys.path.insert(0, str(Path(__file__).parent.parent))

# Import configuration
from core.config import AASConfig

# Import task manager
from core.handoff.task_manager import TaskManager

# Initialize config
try:
    config = AASConfig()
except Exception as e:
    print(f"Config error: {e}")
    sys.exit(1)

# Initialize task manager
try:
    tm = TaskManager(config)
except Exception as e:
    print(f"TaskManager error: {e}")
    sys.exit(1)

# Finally, do the actual work
task = tm.claim_task(actor_name="MyScript")
if task:
    print(f"Claimed: {task['id']}")
else:
    print("No tasks available")
```

**Lines of code:** 31 lines (19 setup, 12 logic)  
**Boilerplate:** 61% of the file

### ✅ After (With ManagerHub)

```python
# File: scripts/my_task_script.py
from core.managers import ManagerHub

hub = ManagerHub.create()

# Do the actual work
task = hub.tasks.claim_task(actor_name="MyScript")
if task:
    print(f"Claimed: {task['id']}")
else:
    print("No tasks available")
```

**Lines of code:** 9 lines (2 setup, 7 logic)  
**Boilerplate:** 22% of the file  
**Reduction:** 71% fewer lines

---

## Example 2: Multi-Manager Script

### ❌ Before (Current Pattern)

```python
# File: scripts/complex_workflow.py
import sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).parent.parent))

from core.config import AASConfig
from core.handoff.task_manager import TaskManager
from core.batch.manager import BatchManager
from core.db_manager import DatabaseManager

# Initialize everything
config = AASConfig()
tm = TaskManager(config)
batch_mgr = BatchManager(api_key=config.openai_api_key.get_secret_value())
db = DatabaseManager(db_path="artifacts/aas.db")

# Actual workflow
task = tm.claim_task()
if task:
    batch_id = await batch_mgr.submit_batch(...)
    with db.get_session() as session:
        # Save to database
        pass
```

**Lines of code:** 22 lines (13 setup, 9 logic)  
**Boilerplate:** 59%

### ✅ After (With ManagerHub)

```python
# File: scripts/complex_workflow.py
from core.managers import ManagerHub

hub = ManagerHub.create()

# Actual workflow
task = hub.tasks.claim_task()
if task:
    batch_id = await hub.batch.submit_batch(...)
    with hub.db.get_session() as session:
        # Save to database
        pass
```

**Lines of code:** 10 lines (2 setup, 8 logic)  
**Boilerplate:** 20%  
**Reduction:** 55% fewer lines

---

## Example 3: Error Handling

### ❌ Before (Cryptic Errors)

```bash
$ python scripts/my_script.py

Traceback (most recent call last):
  File "scripts/my_script.py", line 8, in <module>
    config = AASConfig()
  File "pydantic/main.py", line 341, in __init__
    __pydantic_validator__.validate_python(data, self_instance=self)
pydantic_core._pydantic_core.ValidationError: 1 validation error for AASConfig
openai_api_key
  Field required [type=missing, input_value={}, input_type=dict]
```

**User Experience:**
- ❌ Technical jargon (pydantic_core, ValidationError)
- ❌ No guidance on how to fix
- ❌ Requires understanding of config internals

### ✅ After (Helpful Errors)

```bash
$ python scripts/my_script.py

⚠️ Configuration Error Detected
============================================================
❌ Missing: OPENAI_API_KEY

   How to fix:
   1. Get your API key from: https://platform.openai.com/api-keys
   2. Add to .env file: OPENAI_API_KEY=sk-...
   3. Or set environment: $env:OPENAI_API_KEY='sk-...'

============================================================
📖 Full documentation: docs/CONFIGURATION.md
```

**User Experience:**
- ✅ Plain English description
- ✅ Step-by-step fix instructions
- ✅ Links to relevant resources

---

## Example 4: CLI Commands

### ❌ Before (Flat Command Structure)

```bash
# List all commands (no grouping)
$ python scripts/task_manager_cli.py --help
Usage: task_manager_cli.py [COMMAND]

Commands:
  list-unbatched          List unbatched tasks
  find-next               Find next claimable
  claim                   Claim a task
  status                  Get task status
  batch                   Batch a task
  batch-all               Batch multiple
  health                  Health summary
  workspace-scan          Scan workspace
  workspace-duplicates    Find duplicates
  workspace-cleanup       Clean temp files
  detect-runaway          Detect runaway
  workspace-defrag        Defragment
  heartbeat               Start heartbeat
  # ... 17+ commands with no organization
```

**Issues:**
- ❌ No logical grouping
- ❌ Hard to find related commands
- ❌ Inconsistent naming

### ✅ After (Grouped Commands)

```bash
# Organized command groups
$ python scripts/aas_cli.py --help
Usage: aas_cli.py [OPTIONS] COMMAND [ARGS]...

  🚀 AAS Unified CLI - Manage tasks, batches, and workspace

Commands:
  task       Task operations (list, claim, status, complete)
  batch      Batch processing (submit, status, results)
  workspace  Workspace health (scan, cleanup, defrag)
  health     Overall system health

# Drill down into groups
$ python scripts/aas_cli.py task --help
Usage: aas_cli.py task [OPTIONS] COMMAND [ARGS]...

  Task management operations

Commands:
  claim     Claim a task
  complete  Mark task as complete
  list      List tasks with filters
  status    Get detailed task status
```

**Benefits:**
- ✅ Logical grouping (task/batch/workspace)
- ✅ Easier to discover commands
- ✅ Tab completion support
- ✅ Consistent naming

---

## Example 5: Configuration Discovery

### ❌ Before (Monolithic Config)

```python
# 248 lines in one file with 30+ fields
class AASConfig(BaseSettings):
    openai_api_key: SecretStr = ...
    openai_model: str = ...
    linear_api_key: Optional[SecretStr] = ...
    linear_team_id: Optional[str] = ...
    responses_api_enabled: bool = ...
    enable_web_search: bool = ...
    enable_file_search: bool = ...
    enable_code_interpreter: bool = ...
    debug_mode: bool = ...
    plugin_dir: str = ...
    artifact_dir: str = ...
    projects: list[Any] = ...
    policy_mode: Literal[...] = ...
    autonomy_level: Literal[...] = ...
    # ... 20+ more fields
```

**Issues:**
- ❌ Overwhelming for new users
- ❌ No clear required vs optional
- ❌ No progressive disclosure

### ✅ After (Tiered Config)

```python
# Clearly separated by importance

# TIER 1: Essential (required to start)
class CoreConfig(BaseSettings):
    openai_api_key: SecretStr  # REQUIRED
    debug_mode: bool = False   # Optional but common

# TIER 2: Optional Integrations
class OptionalConfig(BaseSettings):
    linear_api_key: Optional[SecretStr] = None
    home_assistant_url: Optional[str] = None
    ngrok_enabled: bool = False

# TIER 3: Advanced Settings
class AdvancedConfig(BaseSettings):
    ipc_port: int = 50051
    policy_mode: Literal[...] = "live_advisory"
    autonomy_level: Literal[...] = "advisory"

# Combined for full access
class AASConfig(CoreConfig, OptionalConfig, AdvancedConfig):
    """Complete config with progressive disclosure"""
    pass
```

**Benefits:**
- ✅ New users only see 1-2 required fields
- ✅ Clear separation of concerns
- ✅ Better error messages ("Missing field in CoreConfig")

---

## Example 6: Testing Setup

### ❌ Before (Manual Setup in Each Test)

```python
# tests/test_my_feature.py
import pytest
import tempfile
from core.config import AASConfig
from core.handoff.task_manager import TaskManager
from core.db_manager import DatabaseManager

@pytest.fixture
def setup_managers():
    # Manual setup in every test file
    config = AASConfig(
        openai_api_key="sk-test",
        debug_mode=True
    )
    
    # Create temp database
    temp_db = tempfile.NamedTemporaryFile(delete=False)
    db = DatabaseManager(db_path=temp_db.name)
    db.create_tables()
    
    # Initialize task manager
    tm = TaskManager(config)
    
    yield {'config': config, 'tm': tm, 'db': db}
    
    # Cleanup
    temp_db.close()

def test_my_feature(setup_managers):
    tm = setup_managers['tm']
    # Test code
```

**Issues:**
- ❌ Duplicated setup across test files
- ❌ Manual cleanup required
- ❌ Hard to mock individual managers

### ✅ After (Standard Fixtures)

```python
# tests/test_my_feature.py
import pytest
from tests.fixtures import manager_hub

def test_my_feature(manager_hub):
    # Managers already initialized with test config
    task = manager_hub.tasks.claim_task()
    # Test code
```

```python
# tests/fixtures/managers.py (shared)
import pytest
from core.managers import ManagerHub

@pytest.fixture
def manager_hub(tmp_path):
    """Pre-configured hub with temp database"""
    hub = ManagerHub.create()
    hub.db.db_path = tmp_path / "test.db"
    hub.db.create_tables()
    return hub
```

**Benefits:**
- ✅ Single fixture definition
- ✅ Automatic cleanup
- ✅ Easy to mock: `monkeypatch.setattr(hub, 'batch', mock_batch)`

---

## Example 7: Health Checks

### ❌ Before (Manual Implementation)

```python
# Check if everything is working
def check_health():
    errors = []
    
    try:
        config = AASConfig()
    except Exception as e:
        errors.append(f"Config: {e}")
    
    try:
        tm = TaskManager(config)
        if not tm.board_path.exists():
            errors.append("Task board not found")
    except Exception as e:
        errors.append(f"TaskManager: {e}")
    
    try:
        db = DatabaseManager()
        with db.get_session() as session:
            pass
    except Exception as e:
        errors.append(f"Database: {e}")
    
    if errors:
        print("❌ Health Check Failed:")
        for error in errors:
            print(f"  - {error}")
    else:
        print("✅ All systems healthy")
```

**Issues:**
- ❌ Manual implementation in each script
- ❌ No standard format
- ❌ Limited information

### ✅ After (Built-in Health Checks)

```python
# One-liner health check
from core.managers import ManagerHub

hub = ManagerHub.create()
health = hub.get_health_summary()

print(f"Status: {health['overall_status']}")
# Detailed breakdown available in health dict
```

**Or via CLI:**
```bash
$ python scripts/aas_cli.py health

🏥 AAS System Health Report
============================================================
Timestamp: 2026-01-02T21:07:01
Overall:   HEALTHY

Manager Status:
  ✅ Config          OK
  ✅ Tasks           OK (47 total, 12 queued)
  ✅ Database        OK (connected)
  ✅ Batch           OK (3 active batches)
============================================================
```

**Benefits:**
- ✅ Standard implementation
- ✅ Comprehensive checks
- ✅ CLI and programmatic access

---

## Summary: Impact Comparison

| Metric | Before | After | Improvement |
|--------|--------|-------|-------------|
| **Setup lines** | 10-15 | 2 | 80-87% reduction |
| **Error clarity** | Stack traces | Guided fixes | User-friendly |
| **CLI commands** | 17+ flat | 3 groups | Organized |
| **Config complexity** | 248 lines, 30+ fields | Tiered by importance | Progressive |
| **Test setup** | Manual each time | Standard fixtures | Reusable |
| **Health checks** | Manual implementation | Built-in | Standardized |
| **Time to first script** | 20+ minutes | <5 minutes | 75% faster |

---

## Adoption Path

### Phase 1: Try New Patterns (Non-Breaking)
- Import ManagerHub in new scripts
- Use new CLI for daily tasks
- Old scripts continue working

### Phase 2: Gradual Migration (Optional)
- Migrate high-value scripts first
- Add deprecation warnings
- Update documentation

### Phase 3: Deprecation (Future)
- Mark old patterns deprecated
- Provide auto-migration tools
- Keep support for 1-2 versions

### Phase 4: Removal (Major Version)
- Remove deprecated patterns
- Clean up codebase
- Fully modernized

---

**All improvements are backwards compatible!** Old patterns continue working while new patterns are available for adoption.

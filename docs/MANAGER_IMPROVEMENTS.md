# AAS Manager Ease-of-Use Improvements

**Date:** 2026-01-02  
**Scope:** Developer Experience (DX) and End-User Experience (UX) improvements for AAS managers

---

## Executive Summary

This document outlines critical improvements to streamline the "manager" pattern across AAS, addressing both coding complexity and end-user friction points.

**Priority Focus Areas:**
1. Initialization complexity reduction
2. Unified factory pattern
3. Enhanced error messages
4. Simplified CLI interfaces
5. Better documentation/discoverability

---

## 1. Initialization Complexity

### Current Issues
- **7 different managers** with inconsistent initialization patterns
- Config passed in 3 different ways (no config, kwarg, positional)
- Database paths hardcoded in multiple places
- No clear "entry point" for newcomers

### Proposed Solution: Manager Factory

Create a central `ManagerHub` that handles all manager initialization:

```python
# core/managers/__init__.py
from typing import Optional
from core.config import AASConfig

class ManagerHub:
    """
    Central hub for initializing and accessing all AAS managers.
    Ensures consistent configuration and reduces boilerplate.
    
    Usage:
        # Simple - uses defaults
        hub = ManagerHub.create()
        
        # With custom config
        config = AASConfig()
        hub = ManagerHub.create(config=config)
        
        # Access managers
        hub.tasks.claim_task("AAS-123")
        hub.batch.submit_batch(...)
        hub.db.get_session()
    """
    
    def __init__(self, config: Optional[AASConfig] = None):
        self.config = config or AASConfig()
        self._initialize_managers()
    
    @classmethod
    def create(cls, config: Optional[AASConfig] = None):
        """Factory method for creating hub"""
        return cls(config=config)
    
    def _initialize_managers(self):
        """Lazy-load managers as properties"""
        self._task_manager = None
        self._handoff_manager = None
        self._batch_manager = None
        self._database_manager = None
    
    @property
    def tasks(self) -> 'TaskManager':
        if self._task_manager is None:
            from core.handoff.task_manager import TaskManager
            self._task_manager = TaskManager(self.config)
        return self._task_manager
    
    @property
    def handoff(self) -> 'HandoffManager':
        if self._handoff_manager is None:
            from core.handoff_manager import HandoffManager
            self._handoff_manager = HandoffManager(config=self.config)
        return self._handoff_manager
    
    @property
    def batch(self) -> 'BatchManager':
        if self._batch_manager is None:
            from core.batch.manager import BatchManager
            self._batch_manager = BatchManager(
                api_key=self.config.openai_api_key.get_secret_value()
            )
        return self._batch_manager
    
    @property
    def db(self) -> 'DatabaseManager':
        if self._database_manager is None:
            from core.db_manager import DatabaseManager
            self._database_manager = DatabaseManager(
                db_path="artifacts/aas.db"
            )
        return self._database_manager
```

**Benefits:**
- Single import: `from core.managers import ManagerHub`
- Consistent initialization across all scripts
- Lazy loading (only initialize what you use)
- Easy to mock for testing
- Clear dependency tree

### Migration Path

**Phase 1:** Add `ManagerHub` alongside existing managers (non-breaking)  
**Phase 2:** Update CLI scripts to use hub  
**Phase 3:** Add deprecation warnings to old patterns  
**Phase 4:** Remove deprecated patterns in next major version

---

## 2. Configuration Discoverability

### Current Issues
- 248-line config file with 30+ fields
- No categorization or progressive disclosure
- Users don't know what's required vs optional
- `.env.example` disconnected from actual defaults

### Proposed Solution: Tiered Config

```python
# core/config/tiers.py
from pydantic import BaseSettings, Field

class CoreConfig(BaseSettings):
    """Essential settings required for basic operation"""
    openai_api_key: SecretStr = Field(..., alias="OPENAI_API_KEY")
    debug_mode: bool = Field(default=False, alias="DEBUG_MODE")

class OptionalConfig(BaseSettings):
    """Optional integrations"""
    linear_api_key: Optional[SecretStr] = None
    home_assistant_url: Optional[str] = None
    ngrok_enabled: bool = False

class AdvancedConfig(BaseSettings):
    """Advanced/power-user settings"""
    ipc_port: int = 50051
    policy_mode: Literal["live_advisory", "strict"] = "live_advisory"
    autonomy_level: Literal["advisory", "semi_autonomous"] = "advisory"

class AASConfig(CoreConfig, OptionalConfig, AdvancedConfig):
    """Unified config with progressive disclosure"""
    pass
```

**Benefits:**
- Clear separation of concerns
- New users only see 2-3 required fields
- Power users can explore advanced sections
- Better error messages ("Missing field in CoreConfig")

---

## 3. Error Messages & Debugging

### Current Issues
```python
# Current error (unhelpful)
pydantic.error_wrappers.ValidationError: 1 validation error for AASConfig
openai_api_key
  field required (type=value_error.missing)
```

### Proposed Solution: Enhanced Error Handler

```python
# core/config/validation.py
from loguru import logger

class ConfigValidator:
    @staticmethod
    def validate_or_guide(config_cls):
        """Validate config and provide actionable error messages"""
        try:
            return config_cls()
        except ValidationError as e:
            logger.error("⚠️ Configuration Error Detected")
            logger.error("="*60)
            
            for error in e.errors():
                field = error['loc'][0]
                msg = error['msg']
                
                # Custom guidance
                if field == 'openai_api_key':
                    logger.error(f"❌ Missing: OPENAI_API_KEY")
                    logger.error(f"   How to fix:")
                    logger.error(f"   1. Get API key from: https://platform.openai.com/api-keys")
                    logger.error(f"   2. Add to .env file: OPENAI_API_KEY=sk-...")
                    logger.error(f"   3. Or set environment variable: $env:OPENAI_API_KEY='sk-...'")
                elif field == 'linear_api_key':
                    logger.error(f"⚠️ Optional: LINEAR_API_KEY")
                    logger.error(f"   Feature: Bi-directional Linear sync")
                    logger.error(f"   Skip: Leave blank to disable")
            
            logger.error("="*60)
            logger.error(f"📖 Full docs: docs/CONFIGURATION.md")
            
            raise SystemExit(1)
```

---

## 4. CLI Improvements

### Current Issues
- **17 different CLI commands** in `task_manager_cli.py`
- No grouping or subcommands
- Inconsistent argument naming
- No interactive mode

### Proposed Solution: Click-based CLI with Groups

```python
# scripts/aas.py (new unified CLI)
import click
from core.managers import ManagerHub

@click.group()
@click.option('--debug', is_flag=True, help='Enable debug mode')
@click.pass_context
def cli(ctx, debug):
    """AAS Unified CLI - Manage tasks, batches, and workspace health"""
    ctx.ensure_object(dict)
    ctx.obj['DEBUG'] = debug
    ctx.obj['hub'] = ManagerHub.create()

@cli.group()
def task():
    """Task management commands"""
    pass

@task.command('list')
@click.option('--status', type=click.Choice(['queued', 'in-progress', 'done']))
@click.pass_context
def task_list(ctx, status):
    """List tasks with optional status filter"""
    hub = ctx.obj['hub']
    tasks = hub.tasks.find_tasks(status=status)
    # ... display logic

@task.command('claim')
@click.argument('task_id', required=False)
@click.option('--actor', default='Copilot', help='Actor name')
@click.pass_context
def task_claim(ctx, task_id, actor):
    """Claim a task (auto-selects next if no ID provided)"""
    hub = ctx.obj['hub']
    result = hub.tasks.claim_task(task_id=task_id, actor_name=actor)
    click.echo(f"✅ Claimed: {result['id']} - {result['title']}")

@cli.group()
def batch():
    """Batch processing commands"""
    pass

@batch.command('submit')
@click.argument('task_ids', nargs=-1)
@click.pass_context
def batch_submit(ctx, task_ids):
    """Submit tasks to OpenAI Batch API"""
    # ...

@cli.group()
def workspace():
    """Workspace health & cleanup"""
    pass

@workspace.command('scan')
@click.pass_context
def workspace_scan(ctx):
    """Scan workspace for health issues"""
    # ...

if __name__ == '__main__':
    cli(obj={})
```

**Usage:**
```bash
# New structure
aas task list --status=queued
aas task claim AAS-123
aas task claim  # Auto-selects next

aas batch submit AAS-123 AAS-124
aas batch status batch_abc123

aas workspace scan
aas workspace cleanup --dry-run
```

**Benefits:**
- Logical grouping (task/batch/workspace)
- Tab completion support
- Built-in help (`aas task --help`)
- Consistent UX across all commands

---

## 5. Manager Interface Standardization

### Current Issues
- TaskManager has `claim_task()`, HandoffManager has `claim_next_task()`
- Inconsistent return types (dict vs bool vs Optional[dict])
- No type hints in many places
- Mixed sync/async patterns

### Proposed Solution: Manager Protocol

```python
# core/managers/protocol.py
from typing import Protocol, Optional, Dict, Any, List
from abc import abstractmethod

class ManagerProtocol(Protocol):
    """Standard interface all managers should implement"""
    
    @abstractmethod
    def get_status(self) -> Dict[str, Any]:
        """Return manager health status"""
        ...
    
    @abstractmethod
    def validate(self) -> bool:
        """Validate manager is properly configured"""
        ...

class TaskManagerProtocol(ManagerProtocol):
    """Extended protocol for task managers"""
    
    @abstractmethod
    def claim_task(self, task_id: Optional[str] = None, actor_name: str = "System") -> Optional[Dict[str, str]]:
        """Claim a task by ID or auto-select next"""
        ...
    
    @abstractmethod
    def get_task_status(self, task_id: str) -> Dict[str, Any]:
        """Get detailed task status"""
        ...
    
    @abstractmethod
    def list_tasks(self, status: Optional[str] = None, priority: Optional[str] = None) -> List[Dict[str, Any]]:
        """List tasks with optional filters"""
        ...
```

**Implementation:**
```python
# core/handoff/task_manager.py
class TaskManager(TaskManagerProtocol):
    """Now implements standard protocol"""
    
    def get_status(self) -> Dict[str, Any]:
        return {
            "type": "TaskManager",
            "version": "2.0",
            "tasks_count": len(self.handoff.parse_board()[1]),
            "db_connected": self.db.engine is not None,
            "linear_enabled": self.config.linear_api_key is not None
        }
    
    def validate(self) -> bool:
        try:
            # Check board exists
            assert self.board_path.exists()
            # Check DB connection
            with self.db.get_session() as session:
                pass
            return True
        except Exception as e:
            logger.error(f"Validation failed: {e}")
            return False
```

---

## 6. End-User Experience (Non-Developer)

### Current Issues
- No GUI/Web interface
- Terminal-only interaction
- No visual task board
- Hard to onboard non-technical users

### Proposed Solution: Simple Web Dashboard

```python
# core/web/app.py
from fastapi import FastAPI, Request
from fastapi.templating import Jinja2Templates
from fastapi.staticfiles import StaticFiles

app = FastAPI(title="AAS Dashboard")
templates = Jinja2Templates(directory="core/web/templates")

@app.get("/")
async def dashboard(request: Request):
    hub = ManagerHub.create()
    health = hub.tasks.get_health_summary()
    
    return templates.TemplateResponse("dashboard.html", {
        "request": request,
        "health": health,
        "tasks": hub.tasks.list_tasks(status="queued")
    })

@app.post("/task/{task_id}/claim")
async def claim_task(task_id: str, actor: str = "Web User"):
    hub = ManagerHub.create()
    result = hub.tasks.claim_task(task_id=task_id, actor_name=actor)
    return {"success": True, "task": result}
```

**Features:**
- Visual task board (Kanban-style)
- One-click task claiming
- Health dashboard with charts
- Real-time batch status
- No terminal required

---

## 7. Documentation Improvements

### Current State
- Docs scattered across 12+ markdown files
- No "Getting Started" guide
- No API reference
- Examples disconnected from actual code

### Proposed Structure

```
docs/
├── getting-started/
│   ├── 01-installation.md
│   ├── 02-configuration.md
│   ├── 03-first-task.md
│   └── 04-common-workflows.md
├── managers/
│   ├── task-manager.md       # Full API reference
│   ├── handoff-manager.md
│   ├── batch-manager.md
│   └── database-manager.md
├── cli-reference/
│   ├── aas-task.md
│   ├── aas-batch.md
│   └── aas-workspace.md
└── development/
    ├── architecture.md
    ├── testing.md
    └── contributing.md
```

### Auto-Generated API Docs

```python
# scripts/generate_docs.py
from core.managers import ManagerHub
import inspect

def generate_manager_docs(manager_cls):
    """Generate markdown documentation from docstrings"""
    # Extract class docstring, methods, signatures
    # Generate markdown with examples
    pass
```

---

## 8. Testing & Validation

### Current Issues
- Hard to test manager interactions
- No fixtures or factories
- Each script re-implements setup

### Proposed Solution: Test Utilities

```python
# tests/fixtures/managers.py
import pytest
from core.managers import ManagerHub
from core.config import AASConfig

@pytest.fixture
def mock_config():
    """Config with test values"""
    return AASConfig(
        openai_api_key="sk-test",
        debug_mode=True,
        linear_api_key=None
    )

@pytest.fixture
def manager_hub(mock_config, tmp_path):
    """Hub with temporary database"""
    hub = ManagerHub.create(config=mock_config)
    hub.db.db_path = tmp_path / "test.db"
    hub.db.create_tables()
    return hub

@pytest.fixture
def sample_tasks(manager_hub):
    """Pre-populated task board"""
    manager_hub.tasks.create_task(
        title="Test Task 1",
        priority="High"
    )
    return manager_hub
```

---

## Implementation Priority

### Phase 1: Foundation (Week 1)
- [ ] Create `ManagerHub` factory
- [ ] Add manager validation methods
- [ ] Enhanced error messages

### Phase 2: DX Improvements (Week 2)
- [ ] Unified CLI with Click
- [ ] Manager protocol standardization
- [ ] Test fixtures

### Phase 3: Documentation (Week 3)
- [ ] Getting Started guide
- [ ] API reference per manager
- [ ] CLI reference

### Phase 4: UX (Week 4)
- [ ] Simple web dashboard
- [ ] Visual task board
- [ ] Real-time updates

---

## Metrics for Success

**Developer Metrics:**
- Time to first successful script: < 5 minutes (from clone)
- Lines of boilerplate per script: < 5 lines
- Manager initialization errors: 90% reduction

**End-User Metrics:**
- Non-technical users can claim tasks: Yes (via web UI)
- Time to understand task status: < 30 seconds
- Support tickets for "how do I...": 75% reduction

---

## Backwards Compatibility

All improvements designed to be **additive**:
- Old patterns continue working with deprecation warnings
- New `ManagerHub` coexists with direct imports
- CLI can detect old vs new usage and guide migration

---

## References

- Current managers: `core/{handoff,batch,database}/manager.py`
- CLI: `scripts/task_manager_cli.py`
- Config: `core/config/manager.py`
- Docs: `docs/TASK_MANAGER_GUIDE.md`

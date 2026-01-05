# Efficiency Improvement Drafts for Sixth
**Date:** 2026-01-03  
**Status:** Ready for Review  
**Focus:** Background autonomous work, offline capabilities, reduced API costs

## Context
- OpenAI Batch API is expensive; prefer in-house processing
- Need background task execution without blocking user interaction
- Offline-first approach where possible with minimal network calls
- Current infrastructure: AAS Hub with TaskManager, IPC Bridge, ManagerHub pattern

---

## 🎯 High-Priority: Background Execution Framework

### Draft 1: Async Task Queue with Priority Lanes
**Effort:** 3-4 hours  
**Offline:** 95% (only sync for final reporting)  
**Cost Reduction:** High (eliminates batch API for task orchestration)

**Proposal:**
- Implement `BackgroundWorker` in `core/workers/background.py`
- Priority queues: CRITICAL (immediate), HIGH (5min), NORMAL (30min), LOW (2hr)
- Uses asyncio.Queue with dedicated worker pools per priority
- Tasks persist to SQLite, resume on restart
- Linear sync only on completion/failure

**Key Components:**
```python
class BackgroundWorker:
    def __init__(self, task_manager, max_workers=4):
        self.queues = {priority: asyncio.Queue() for priority in TaskPriority}
        self.workers = {}  # priority -> list of worker tasks
    
    async def enqueue(self, task, priority=TaskPriority.NORMAL):
        await self.queues[priority].put(task)
        # Persist to DB immediately for crash recovery
    
    async def process_queue(self, priority):
        while True:
            task = await self.queues[priority].get()
            await self._execute_offline(task)
```

**Benefits:**
- Zero network calls during execution
- Survives crashes (SQLite persistence)
- Can process 100+ tasks/hour locally

---

### Draft 2: Local LLM Task Decomposition
**Effort:** 4-5 hours  
**Offline:** 100%  
**Cost Reduction:** Extreme (replaces GPT-4 for decomposition)

**Proposal:**
- Use Ollama (already in codebase: `scripts/test_ollama.py`)
- Models: `deepseek-coder:6.7b` for code tasks, `llama3.1:8b` for planning
- Decompose Linear issues into subtasks offline
- Only call OpenAI API for final code review/validation

**Architecture:**
```
Linear Issue → Local LLM Decomposition → Subtask Queue → 
Background Execution → Local Validation → OpenAI Final Check (optional)
```

**Example Flow:**
1. AAS-213 "Live Event Stream" → Ollama analyzes
2. Generates: [FastAPI setup, WebSocket handler, gRPC integration, tests]
3. Each subtask executed by BackgroundWorker
4. Final PR review can use GPT-4 (1 call vs. 10+)

**Cost Savings:** ~$5-15 per complex task

---

### Draft 3: Cron-Style Maintenance Tasks
**Effort:** 2 hours  
**Offline:** 100%  
**Cost Reduction:** N/A (infrastructure)

**Proposal:**
- `ScheduledTasks` manager in `core/managers/scheduler.py`
- Runs background maintenance without user interaction
- Schedule: Type checking (hourly), test suite (daily 3am), defrag (weekly)

**Tasks:**
```yaml
scheduled_tasks:
  - name: "type_check"
    schedule: "0 * * * *"  # Hourly
    command: "mypy core/ plugins/"
    report_to: artifacts/health/type_errors.json
  
  - name: "test_suite"
    schedule: "0 3 * * *"  # Daily 3am
    command: "pytest tests/"
    report_to: artifacts/health/test_results.json
  
  - name: "defrag_workspace"
    schedule: "0 2 * * 0"  # Sunday 2am
    command: "pwsh scripts/defrag_workspace.ps1"
```

**Benefits:**
- Issues discovered proactively
- Zero API costs
- Runs while user sleeps

---

## 🔧 Medium-Priority: Code Quality Automation

### Draft 4: Self-Healing Import Resolver
**Effort:** 3 hours  
**Offline:** 100%  
**Cost Reduction:** Medium (reduces debug iterations)

**Proposal:**
- Detect missing imports via mypy output
- Use AST analysis to locate definitions
- Auto-generate import statements
- Create PR with fixes

**Implementation:**
```python
# core/tools/import_fixer.py
def resolve_missing_imports(mypy_output):
    for error in parse_mypy_errors(mypy_output):
        if "Cannot find implementation" in error:
            module = find_module_containing(error.symbol)
            if module:
                add_import(error.file, module, error.symbol)
```

**Addresses Current Issues:**
- `core.handoff.manager` missing → auto-fix to `core.managers.tasks`
- `core.managers.health` missing → create stub or redirect

---

### Draft 5: SQLAlchemy Query Linter
**Effort:** 2-3 hours  
**Offline:** 100%  
**Cost Reduction:** Low (prevents runtime bugs)

**Proposal:**
- AST walker to detect `if column_obj` patterns
- Auto-rewrite to `if column_obj.value` or proper query
- Fixes 5 current errors in `core/managers/tasks.py`

**Example Transform:**
```python
# Before
if task.status != TaskStatus.QUEUED:  # Error: comparing Column to enum

# After
if task.status.value != TaskStatus.QUEUED.value:
# OR
if session.query(Task).filter(Task.status != TaskStatus.QUEUED).count():
```

---

### Draft 6: Test File Organizer
**Effort:** 1-2 hours  
**Offline:** 100%  
**Cost Reduction:** N/A (infrastructure)

**Proposal:**
- Scan `scripts/test_*.py` → move to `tests/`
- Preserve git history with `git mv`
- Update imports automatically
- Generate `tests/conftest.py` with shared fixtures

**Automation:**
```bash
# scripts/organize_tests.py
for file in scripts/test_*.py:
    new_path = tests/$(basename $file)
    git mv $file $new_path
    update_imports($new_path)
```

---

## 💾 High-Priority: Local Processing Pipeline

### Draft 7: Embedded Vector Search (Offline RAG)
**Effort:** 5-6 hours  
**Offline:** 100% after initial indexing  
**Cost Reduction:** Extreme (no OpenAI embeddings)

**Proposal:**
- Use `sentence-transformers` (local embeddings)
- Index codebase into ChromaDB/FAISS
- Semantic code search without API calls
- Update index on file changes (background task)

**Use Cases:**
- Find similar code patterns
- Locate relevant tests for new features
- Identify refactoring candidates

**Storage:**
```
artifacts/vector_db/
  └── embeddings.faiss  # ~50MB for entire codebase
```

---

### Draft 8: Local Code Analysis Pipeline
**Effort:** 4 hours  
**Offline:** 100%  
**Cost Reduction:** High (replaces GPT-4 for code understanding)

**Proposal:**
- AST-based code analysis (complexity, dependencies, duplication)
- Generate insights without LLM calls
- Detect code smells: long functions (>50 lines), high cyclomatic complexity (>10), duplicate blocks (>5 lines)

**Output:**
```json
{
  "file": "core/managers/tasks.py",
  "issues": [
    {"type": "complexity", "function": "claim_task", "score": 12},
    {"type": "duplication", "lines": [145, 167], "similarity": 0.87}
  ],
  "suggestions": [
    "Extract claim_task validation to separate function",
    "Consolidate duplicate query patterns"
  ]
}
```

---

### Draft 9: In-House Test Generation
**Effort:** 6-8 hours  
**Offline:** 90% (can use local LLM)  
**Cost Reduction:** Extreme (replaces GPT-4 test generation)

**Proposal:**
- AST analysis to identify untested functions
- Template-based test generation (pytest fixtures, mocks)
- Use local LLM (deepseek-coder) for edge cases
- Only use GPT-4 for complex integration tests

**Template System:**
```python
# For function: async def claim_task(task_id, agent_id)
# Generate:
@pytest.mark.asyncio
async def test_claim_task_success():
    task_manager = TaskManager(db_manager, ipc)
    result = await task_manager.claim_task("task-1", "agent-1")
    assert result is not None
    assert result.claimed_by == "agent-1"
```

**Target:** 80% coverage without API costs

---

## 🚀 Medium-Priority: Workflow Optimization

### Draft 10: Smart Branch Manager
**Effort:** 3 hours  
**Offline:** 95% (only push at end)  
**Cost Reduction:** Medium (reduces coordination overhead)

**Proposal:**
- Auto-create branches from Linear issues: `AAS-213` → `maelstrom/live-event-stream`
- Commit atomic changes as work progresses
- Auto-rebase on main before PR
- Draft PR creation with AI-generated description (local LLM)

**Workflow:**
```
1. Sixth starts AAS-213
2. Branch auto-created: maelstrom/live-event-stream
3. Each subtask → atomic commit
4. On completion: rebase, push, create PR
5. Local LLM writes PR description from commit history
```

---

### Draft 11: Incremental Type Checking
**Effort:** 2-3 hours  
**Offline:** 100%  
**Cost Reduction:** Low (speeds up development)

**Proposal:**
- Only type-check changed files (not entire codebase)
- Cache mypy results in `.mypy_cache/`
- Background daemon watches for file changes
- Report errors to `artifacts/health/type_errors.json`

**Performance:**
- Current: 45s for full check
- Incremental: 3-5s per file change

---

### Draft 12: Dependency Graph Visualizer
**Effort:** 3-4 hours  
**Offline:** 100%  
**Cost Reduction:** N/A (planning tool)

**Proposal:**
- Parse imports to build module dependency graph
- Detect circular dependencies
- Identify "god modules" (imported by >10 modules)
- Export to Graphviz/D3.js

**Output:**
```
artifacts/diagrams/dependency_graph.html
- core.managers.tasks → [core.database, core.ipc, core.config]
- Circular: core.ipc.server ↔ core.managers.tasks
```

---

## 📊 Low-Priority: Monitoring & Observability

### Draft 13: Lightweight Telemetry System
**Effort:** 4 hours  
**Offline:** 100% (local storage)  
**Cost Reduction:** N/A (observability)

**Proposal:**
- Track task execution times, error rates, resource usage
- Store in SQLite: `artifacts/telemetry.db`
- Dashboard: `artifacts/telemetry/dashboard.html`
- No external services (Datadog, New Relic)

**Metrics:**
```json
{
  "task_execution_time": {"avg": 234ms, "p95": 890ms},
  "ipc_requests_per_minute": 45,
  "error_rate_24h": 0.02,
  "top_errors": ["ImportError: core.handoff.manager", ...]
}
```

---

### Draft 14: Health Check Endpoint
**Effort:** 2 hours  
**Offline:** 100%  
**Cost Reduction:** N/A (infrastructure)

**Proposal:**
- `/health` endpoint in FastAPI
- Returns: DB connection, IPC status, task queue depth, last error
- Can be polled by external monitors or user scripts

**Response:**
```json
{
  "status": "healthy",
  "database": "connected",
  "ipc": "serving on :50051",
  "task_queue": {"queued": 3, "in_progress": 1},
  "last_error": "2026-01-03T14:23:45Z - ImportError in tasks.py"
}
```

---

### Draft 15: Auto-Generated Changelog
**Effort:** 2-3 hours  
**Offline:** 100%  
**Cost Reduction:** N/A (documentation)

**Proposal:**
- Parse git commits (conventional format: `feat:`, `fix:`)
- Group by type and generate `CHANGELOG.md`
- Update on each PR merge (git hook)

**Example:**
```markdown
## [Unreleased]
### Added
- gRPC Task Broadcasting (AAS-114)
- File size management strategy

### Fixed
- Git history cleanup (removed 218MB exe)
```

---

## 🧪 High-Priority: Testing Infrastructure

### Draft 16: Mutation Testing (Offline Quality Check)
**Effort:** 5 hours  
**Offline:** 100%  
**Cost Reduction:** Medium (improves test quality)

**Proposal:**
- Use `mutmut` to mutate code and verify tests catch changes
- Run nightly as background task
- Report weak test coverage areas

**Example:**
```python
# Original: if status == TaskStatus.QUEUED
# Mutant: if status != TaskStatus.QUEUED
# If tests pass → weak test coverage
```

**Output:** "Tests don't cover status transition from QUEUED to CLAIMED"

---

### Draft 17: Property-Based Testing Generator
**Effort:** 4-5 hours  
**Offline:** 100%  
**Cost Reduction:** High (more robust than unit tests)

**Proposal:**
- Use `hypothesis` for property-based tests
- Generate random inputs to find edge cases
- Example: TaskManager.claim_task with random task IDs, agent IDs, states

**Generated Test:**
```python
from hypothesis import given, strategies as st

@given(
    task_id=st.text(min_size=1, max_size=50),
    agent_id=st.text(min_size=1, max_size=50)
)
async def test_claim_task_idempotency(task_id, agent_id):
    result1 = await task_manager.claim_task(task_id, agent_id)
    result2 = await task_manager.claim_task(task_id, agent_id)
    assert result1 == result2  # Should be idempotent
```

---

### Draft 18: Snapshot Testing for Config/Protos
**Effort:** 2 hours  
**Offline:** 100%  
**Cost Reduction:** Low (prevents breaking changes)

**Proposal:**
- Snapshot `core/config/manager.py` schema
- Snapshot `core/ipc/protos/bridge.proto` definitions
- Fail tests if schemas change unexpectedly

**Use Case:**
- Prevent accidental removal of config fields
- Detect proto breaking changes before deploying

---

## 🔄 Medium-Priority: Automation Workflows

### Draft 19: Self-Updating Documentation
**Effort:** 3-4 hours  
**Offline:** 100%  
**Cost Reduction:** N/A (maintenance)

**Proposal:**
- Docstring extraction to generate API docs
- Update `docs/` on each commit (pre-commit hook)
- Use `pdoc` or `sphinx` for HTML generation

**Automation:**
```bash
# .git/hooks/pre-commit
python -m pdoc core/ plugins/ --html --output-dir docs/api/
git add docs/api/
```

---

### Draft 20: Background Task Recovery System
**Effort:** 4 hours  
**Offline:** 100%  
**Cost Reduction:** High (reduces failed task waste)

**Proposal:**
- Persist task state to SQLite every 30s
- On crash: resume from last checkpoint
- Exponential backoff for retries (1s, 2s, 4s, 8s)

**Implementation:**
```python
class RecoverableTask:
    def __init__(self, task_id, checkpoint_interval=30):
        self.checkpoint_interval = checkpoint_interval
    
    async def execute_with_checkpoints(self, work_fn):
        checkpoint = load_checkpoint(self.task_id)
        if checkpoint:
            resume_from = checkpoint["progress"]
        
        async for progress in work_fn(resume_from):
            save_checkpoint(self.task_id, progress)
            await asyncio.sleep(self.checkpoint_interval)
```

**Benefits:**
- No lost work on crashes
- Can pause/resume long-running tasks
- Survives system reboots

---

## 📋 Summary Matrix

| Draft | Effort | Offline | Cost Savings | Priority | Dependencies |
|-------|--------|---------|--------------|----------|--------------|
| 1. Background Task Queue | 3-4h | 95% | High | ⭐⭐⭐ | SQLite, asyncio |
| 2. Local LLM Decomposition | 4-5h | 100% | Extreme | ⭐⭐⭐ | Ollama, test_ollama.py |
| 3. Cron Maintenance | 2h | 100% | N/A | ⭐⭐ | APScheduler |
| 4. Import Resolver | 3h | 100% | Medium | ⭐⭐⭐ | mypy, AST |
| 5. SQLAlchemy Linter | 2-3h | 100% | Low | ⭐⭐ | AST |
| 6. Test Organizer | 1-2h | 100% | N/A | ⭐⭐ | git |
| 7. Vector Search | 5-6h | 100% | Extreme | ⭐⭐⭐ | sentence-transformers |
| 8. Code Analysis | 4h | 100% | High | ⭐⭐ | AST, radon |
| 9. Test Generation | 6-8h | 90% | Extreme | ⭐⭐⭐ | deepseek-coder |
| 10. Branch Manager | 3h | 95% | Medium | ⭐⭐ | git, Linear API |
| 11. Incremental TypeCheck | 2-3h | 100% | Low | ⭐⭐ | mypy daemon |
| 12. Dependency Graph | 3-4h | 100% | N/A | ⭐ | graphviz |
| 13. Telemetry | 4h | 100% | N/A | ⭐ | SQLite |
| 14. Health Endpoint | 2h | 100% | N/A | ⭐⭐ | FastAPI |
| 15. Auto Changelog | 2-3h | 100% | N/A | ⭐ | git |
| 16. Mutation Testing | 5h | 100% | Medium | ⭐⭐ | mutmut |
| 17. Property Testing | 4-5h | 100% | High | ⭐⭐ | hypothesis |
| 18. Snapshot Tests | 2h | 100% | Low | ⭐ | pytest |
| 19. Auto Docs | 3-4h | 100% | N/A | ⭐ | pdoc |
| 20. Recovery System | 4h | 100% | High | ⭐⭐⭐ | SQLite, asyncio |

**Legend:**
- ⭐⭐⭐ = Critical for cost reduction/automation
- ⭐⭐ = High value
- ⭐ = Nice to have

---

## 🎯 Recommended Implementation Order

### Phase 1: Foundation (8-10 hours)
1. **Draft 1:** Background Task Queue → enables all other automation
2. **Draft 20:** Recovery System → prevents lost work
3. **Draft 4:** Import Resolver → fixes current blockers

### Phase 2: Cost Reduction (10-13 hours)
4. **Draft 2:** Local LLM Decomposition → biggest cost savings
5. **Draft 7:** Vector Search → eliminates embedding costs
6. **Draft 9:** Test Generation → automated quality

### Phase 3: Maintenance (6-8 hours)
7. **Draft 3:** Cron Tasks → automated health checks
8. **Draft 6:** Test Organizer → infrastructure cleanup
9. **Draft 14:** Health Endpoint → observability

### Phase 4: Advanced (12-15 hours)
10. **Draft 10:** Branch Manager → workflow automation
11. **Draft 16:** Mutation Testing → quality assurance
12. **Draft 17:** Property Testing → robust testing

**Total Effort:** 36-46 hours (~1 week of work)  
**Expected Cost Savings:** $200-500/month in API costs  
**Background Execution:** 95%+ of work runs offline

---

## 🔑 Key Success Metrics

1. **API Cost Reduction:** Target 70% reduction in OpenAI API calls
2. **Automation Coverage:** 80% of routine tasks automated
3. **Crash Recovery:** 100% task resumption after crashes
4. **Offline Operation:** 95% functionality without network
5. **Background Processing:** 90% of tasks run without user interaction

---

## 📝 Next Steps for Sixth

1. **Review Drafts:** Identify top 5 highest-impact for immediate implementation
2. **Assess Dependencies:** Verify Ollama setup, check SQLite schema
3. **Create Tasks:** Break chosen drafts into Linear issues
4. **Start with Draft 1:** Background task queue enables everything else
5. **Report Progress:** Update `ACTIVE_TASKS.md` with hourly checkpoints

**Questions for Sixth:**
1. Which drafts align best with current roadmap priorities?
2. Are there any technical blockers (missing dependencies)?
3. Should we parallelize Drafts 1+4 (foundation fixes)?
4. Preferred local LLM model (deepseek-coder vs llama3.1)?
5. Timeline constraint: implement all in 1 week or prioritize top 5?

---

**Saved:** 2026-01-03 (Pre-Restart Checkpoint)  
**Status:** Ready for Sixth's review upon restart  
**Contact:** Copilot for clarifications on any draft

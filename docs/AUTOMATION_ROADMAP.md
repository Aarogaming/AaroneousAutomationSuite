# Full Automation Pipeline - Implementation Plan

> **Part of**: [MASTER_ROADMAP.md](MASTER_ROADMAP.md) § Phase 2.1 - Batch Processing & Task Automation

## Current State Analysis

### ✅ What's Working
1. **Batch Submission** - `batch_monitor.py` (running, 60s intervals)
   - Auto-scans for queued tasks
   - Submits batches to OpenAI
   - Tracks state to prevent duplicates

2. **Batch Retrieval** - `retrieve_both_batches.py`
   - Downloads completed results
   - Saves to `artifacts/batch/results/`
   - Parses JSON responses

3. **Existing Tools**:
   - `core/handoff/agents/argo_client.py` - Task decomposition framework (not fully integrated)
   - `scripts/batch_implementer.py` - Code extraction from batch results (semi-manual)
   - `scripts/batch_recycler.py` - Result parsing utilities

### ❌ What's Missing (Priority Order)

## 1. **Automated Implementation Engine** (HIGHEST PRIORITY)
**Goal**: Convert batch analysis → actual code files automatically

**Current Gap**: `batch_implementer.py` only extracts code blocks, doesn't apply them

**Required Components**:
```
core/automation/
├── implementation_engine.py    # Main orchestrator
├── code_generator.py          # Generate files from batch analysis
├── file_applier.py            # Safe file creation/editing
└── validation.py              # Pre/post-implementation checks
```

**Features Needed**:
- Parse batch results into structured implementation plans
- Map analysis → file paths (plugins/, core/, etc.)
- Generate boilerplate (classes, imports, docstrings)
- Apply changes with git safety (create branch, commit)
- Run tests after implementation
- Auto-update ACTIVE_TASKS.md status

**Estimated Complexity**: High (3-5 days)
**Cost Savings**: Eliminates 90% of manual implementation work

---

## 2. **Task Decomposition Integration** (HIGH PRIORITY)
**Goal**: AAS-211 - Break complex goals into sub-tasks automatically

**Current State**: 
- ✅ `argo_client.py` exists with decomposition logic
- ❌ Not integrated with HandoffManager
- ❌ No API to trigger from CLI/UI

**Required Changes**:
```python
# In core/handoff/manager.py
def decompose_task(self, task_id: str) -> List[str]:
    """
    Decompose a task into sub-tasks using ARGO/GPT-4.
    Returns list of new sub-task IDs added to ACTIVE_TASKS.md
    """
    # 1. Get task details from board
    # 2. Call ARGO decompose_task() or batch API
    # 3. Parse sub-tasks with dependencies
    # 4. Add to ACTIVE_TASKS.md as "Queued"
    # 5. Update parent task with sub-task references
    # 6. Return new task IDs
```

**CLI Command**: 
```bash
python scripts/task_manager_cli.py decompose AAS-211
# Output: Created AAS-211-1, AAS-211-2, AAS-211-3
```

**Estimated Complexity**: Medium (1-2 days)
**Unblocks**: Infinite task generation from high-level goals

---

## 3. **End-to-End Orchestration** (MEDIUM PRIORITY)
**Goal**: Single command to go from goal → implemented code

**Workflow**:
```
User Input: "Build voice-controlled Wizard101 commands"
    ↓
1. Decompose into sub-tasks (AAS-211)
    ↓ (creates AAS-400, AAS-401, AAS-402 in "Queued" status)
2. Batch monitor picks them up (60s scan)
    ↓
3. Submit batch for analysis
    ↓ (OpenAI processes ~2min-2hrs)
4. Retrieve results when complete
    ↓
5. Implementation engine converts to code
    ↓ (creates files, commits, runs tests)
6. Update tasks to "Done" in ACTIVE_TASKS.md
    ↓
7. Notify user via webhook/Linear
```

**Required**:
- Master orchestrator: `core/automation/orchestrator.py`
- Webhook system for completion notifications
- Rollback mechanism for failed implementations

**Estimated Complexity**: Medium (2-3 days)
**Value**: Full autonomous development loop

---

## 4. **Quality Assurance Layer** (LOW PRIORITY)
**Goal**: Validate implementations before marking "Done"

**Checks**:
- Syntax validation (compile check)
- Import resolution (all imports available?)
- Type checking (mypy)
- Test execution (if tests exist)
- Integration smoke test (does it load in Hub?)

**Implementation**:
```
core/automation/qa/
├── syntax_validator.py
├── import_checker.py
├── test_runner.py
└── smoke_test.py
```

**Estimated Complexity**: Low (1 day)
**Value**: Reduces broken code commits

---

## Implementation Priority Queue

### Phase 1: Core Automation (Week 1)
**Deliverable**: Batch results → working code automatically

Tasks:
1. ✅ AAS-211-1: Create `core/automation/implementation_engine.py`
2. ✅ AAS-211-2: Create `core/automation/code_generator.py`
3. ✅ AAS-211-3: Integrate with `batch_monitor.py`
4. ✅ AAS-211-4: Add git safety (branch creation, commits)

**Success Metric**: Run batch → Get working plugin without manual coding

---

### Phase 2: Task Decomposition (Week 2)
**Deliverable**: High-level goals → actionable sub-tasks

Tasks:
1. ✅ AAS-211-5: Integrate `argo_client.py` with HandoffManager
2. ✅ AAS-211-6: Add `decompose_task()` method
3. ✅ AAS-211-7: Create CLI command `aas task decompose`
4. ✅ AAS-211-8: Add dependency graph validation

**Success Metric**: "Build X feature" → 5-10 queued sub-tasks

---

### Phase 3: Orchestration (Week 3)
**Deliverable**: Full autonomous loop

Tasks:
1. ✅ AAS-211-9: Create master orchestrator
2. ✅ AAS-211-10: Add webhook notifications
3. ✅ AAS-211-11: Implement rollback mechanism
4. ✅ AAS-211-12: Add monitoring dashboard

**Success Metric**: Single goal → fully implemented feature autonomously

---

## Quick Wins (Can Start Now)

### Immediate Action Items:

**1. Enhance `batch_monitor.py`** (30 min)
Add result processing hook:
```python
async def _process_batch_results(self, batch_id: str):
    # Download results
    results = await self._retrieve_results(batch_id)
    
    # NEW: Auto-apply implementations
    from core.automation.implementation_engine import ImplementationEngine
    engine = ImplementationEngine()
    await engine.process_batch(batch_id, results)
```

**2. Create Stub Implementation Engine** (1 hour)
Minimal version that creates placeholder files:
```python
# core/automation/implementation_engine.py
class ImplementationEngine:
    async def process_batch(self, batch_id, results):
        for task_id, analysis in results.items():
            # Parse analysis
            plan = self._parse_analysis(analysis)
            
            # Generate files
            for file_spec in plan.files:
                self._create_file(file_spec)
            
            # Update task status
            self._mark_done(task_id)
```

**3. Test with AAS-014** (2 hours)
Use DanceBot as test case since code already exists:
- Run batch analysis (already have results)
- Test implementation engine on known-good structure
- Validate against existing `Wizard101_DanceBot/` code

---

## Cost/Benefit Analysis

### Manual Implementation (Current)
- Time per task: 2-4 hours
- Cost: Developer time (~$100-200/task)
- Error rate: ~20% (typos, missing imports, etc.)
- Throughput: 2-3 tasks/day

### Automated Implementation (Target)
- Time per task: 5-10 minutes (batch processing)
- Cost: $0.015/task (batch API) + validation compute
- Error rate: ~5% (with QA layer)
- Throughput: 20+ tasks/day

**ROI**: 95% time savings, 50% cost savings, 3x throughput

---

## Next Steps (Choose One)

### Option A: Quick Prototype (2-4 hours)
Build minimal implementation engine and test on AAS-014

### Option B: Full AAS-211 Implementation (1-2 days)
Complete task decomposition system first, then add auto-implementation

### Option C: Hybrid Approach (6-8 hours)
1. Stub implementation engine (generates TODO files)
2. Basic decomposition integration
3. Test end-to-end with simple task

**Recommended**: **Option C** - Gets full pipeline working ASAP with placeholders, then improve incrementally.

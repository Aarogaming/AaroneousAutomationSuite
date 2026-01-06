# Handoff Document: AAS-228 - Integration Engine

**Task ID**: AAS-228  
**Priority**: High  
**Status**: Queued  
**Created**: 2026-01-03  
**Dependencies**: AAS-227 (Implementation Engine), AAS-211 (Task Decomposition)

---

## Executive Summary

Build a master orchestration system that connects all automation components into a single autonomous development pipeline. This is the **final piece** that enables: **"User states goal → AI implements feature → Code deployed"** with zero manual intervention.

**Expected Impact**:
- **Full autonomy**: High-level goals become working code automatically
- **Compound efficiency**: Combines task decomposition + batch processing + auto-implementation
- **Scalable development**: Handle 100+ tasks/week with AI agents
- **Self-improving system**: Learn from implementations to improve future ones

---

## Vision: Complete Automation Loop

### Current State (Manual)
```
User: "Build voice-controlled Wizard101 commands"
  ↓
Developer manually:
1. Break into sub-tasks (30 min)
2. Write implementation plan (1 hour)
3. Code each component (4-8 hours)
4. Test and debug (2 hours)
5. Document and deploy (1 hour)

Total: 8-12 hours human time
```

### Target State (Automated)
```
User: "Build voice-controlled Wizard101 commands"
  ↓
aas automate "Build voice-controlled Wizard101 commands"
  ↓
Integration Engine:
1. Decompose into sub-tasks [2 min]
   → Creates AAS-400, AAS-401, AAS-402, AAS-403
2. Batch submit for analysis [30 sec]
   → OpenAI processes 4 tasks
3. Wait for completion [10-120 min]
   → Monitor checks every 5 min
4. Auto-implement results [5 min per task]
   → 4 plugins/services created
5. Validate and test [2 min]
   → Syntax, imports, smoke tests
6. Commit and deploy [1 min]
   → Git commit, update ACTIVE_TASKS.md
7. Notify user [instant]
   → Discord/Linear notification

Total: ~20-130 minutes, 99% automated
```

---

## Architecture Overview

### Component Diagram
```
┌─────────────────────────────────────────────────────────┐
│              Integration Engine (Orchestrator)          │
│                                                          │
│  ┌────────────────────────────────────────────────┐   │
│  │  Pipeline Coordinator                          │   │
│  │  - State machine for workflow stages           │   │
│  │  - Error handling and recovery                 │   │
│  │  - Progress tracking and reporting             │   │
│  └────────────────────────────────────────────────┘   │
└─────────────────────────────────────────────────────────┘
         │                 │                 │
         ▼                 ▼                 ▼
┌─────────────────┐ ┌─────────────────┐ ┌─────────────────┐
│ Task            │ │ Batch           │ │ Implementation  │
│ Decomposition   │ │ Processing      │ │ Engine          │
│                 │ │                 │ │                 │
│ - ARGO Client   │ │ - Batch Monitor │ │ - Code Gen      │
│ - HandoffMgr    │ │ - Batch Manager │ │ - File Apply    │
│ - Dependency    │ │ - Result Parser │ │ - Validation    │
│   Resolution    │ │                 │ │                 │
└─────────────────┘ └─────────────────┘ └─────────────────┘
         │                 │                 │
         └─────────────────┴─────────────────┘
                           │
                           ▼
              ┌───────────────────────────┐
              │  Supporting Services      │
              │  - Git Manager            │
              │  - Test Runner            │
              │  - Notification System    │
              │  - Linear Sync            │
              └───────────────────────────┘
```

---

## Technical Specification

### File Structure
```
core/automation/
├── orchestrator.py           # IntegrationEngine class (main)
├── pipeline.py               # Pipeline state machine
├── stages/                   # Individual pipeline stages
│   ├── decompose_stage.py
│   ├── batch_stage.py
│   ├── implement_stage.py
│   ├── validate_stage.py
│   └── deploy_stage.py
├── notifications.py          # Webhook/notification system
├── recovery.py               # Error handling and rollback
└── monitoring.py            # Pipeline monitoring and metrics
```

### Data Models

#### Pipeline State
```python
@dataclass
class PipelineRun:
    id: str
    goal: str
    created_at: datetime
    status: PipelineStatus
    current_stage: str
    progress: float  # 0.0 to 1.0
    tasks_created: List[str]
    tasks_completed: List[str]
    batch_ids: List[str]
    error: Optional[str]
    metadata: Dict[str, Any]

class PipelineStatus(Enum):
    QUEUED = "queued"
    DECOMPOSING = "decomposing"
    BATCHING = "batching"
    WAITING = "waiting"
    IMPLEMENTING = "implementing"
    VALIDATING = "validating"
    DEPLOYING = "deploying"
    COMPLETED = "completed"
    FAILED = "failed"
    PAUSED = "paused"
```

#### Stage Result
```python
@dataclass
class StageResult:
    stage: str
    status: str  # "success", "failure", "partial"
    output: Any
    errors: List[str]
    warnings: List[str]
    metrics: Dict[str, Any]
    next_stage: Optional[str]
```

---

## Pipeline Stages

### Stage 1: Decompose
**Input**: High-level goal string  
**Output**: List of task IDs created in ACTIVE_TASKS.md

**Process**:
1. Call `ARGOClient.decompose_task(goal)`
2. Parse sub-tasks with dependencies
3. Add to ACTIVE_TASKS.md as "Queued"
4. Return task IDs for tracking

**Example**:
```python
Input: "Build voice-controlled Wizard101 commands"
Output: ["AAS-400", "AAS-401", "AAS-402", "AAS-403"]
Tasks created:
- AAS-400: Integrate Home Assistant voice recognition
- AAS-401: Create voice command parser
- AAS-402: Map voice commands to Wizard101 actions
- AAS-403: Implement voice feedback system
```

---

### Stage 2: Batch
**Input**: List of task IDs  
**Output**: Batch ID(s) submitted to OpenAI

**Process**:
1. Call `HandoffManager.batch_analyze_queued_tasks(task_ids)`
2. Submit to OpenAI Batch API
3. Store batch ID in pipeline state
4. Return batch IDs for monitoring

**Considerations**:
- Max 20 tasks per batch (OpenAI limit)
- Multiple batches if >20 tasks
- Track batch submissions in monitor_state.json

---

### Stage 3: Wait
**Input**: Batch ID(s)  
**Output**: Completed batch results

**Process**:
1. Poll OpenAI API every 5 minutes
2. Check batch completion status
3. When complete, retrieve results
4. Return results for implementation

**Options**:
- Timeout after 24 hours (OpenAI max)
- Allow pause/resume if user intervenes
- Notify user of long wait times

---

### Stage 4: Implement
**Input**: Batch results  
**Output**: Created/modified files

**Process**:
1. Call `ImplementationEngine.process_batch(batch_id)`
2. For each task:
   - Parse analysis
   - Generate code
   - Apply files
3. Collect implementation reports
4. Return summary

**Rollback on Failure**:
- Keep git branches for each implementation
- Revert failed implementations
- Mark tasks as "Needs Review" in ACTIVE_TASKS.md

---

### Stage 5: Validate
**Input**: List of implemented task IDs  
**Output**: Validation results

**Process**:
1. For each implementation:
   - Syntax check (compile)
   - Import resolution
   - Type checking (mypy)
   - Test execution (if tests exist)
2. Smoke test: try loading in Hub
3. Collect validation reports
4. Fail pipeline if critical errors

**Quality Gates**:
- Must pass: Syntax, imports
- Should pass: Type checks, tests
- Optional: Performance benchmarks

---

### Stage 6: Deploy
**Input**: Validated implementations  
**Output**: Deployed code in main branch

**Process**:
1. Merge implementation branches to master (or create PR)
2. Update ACTIVE_TASKS.md: mark tasks "Done"
3. Tag release if significant feature
4. Trigger CI/CD if configured
5. Return deployment summary

**Safety**:
- Require manual approval for prod deployments
- Auto-deploy to dev/staging environments
- Create rollback tags before deployment

---

### Stage 7: Notify
**Input**: Pipeline run summary  
**Output**: Notifications sent

**Process**:
1. Format completion report
2. Send to configured channels:
   - Discord webhook
   - Linear comment
   - Email (optional)
3. Include: tasks completed, files created, validation results
4. Add links to git commits

---

## Integration Points

### 1. CLI Interface
**File**: `scripts/aas_cli.py` (extend existing)

**New Command**:
```bash
# Full automation
aas automate "Build voice-controlled Wizard101 commands"

# With options
aas automate "Build X" --priority high --assignee Sixth --dry-run

# Resume paused pipeline
aas automate resume <pipeline_id>

# Check pipeline status
aas automate status <pipeline_id>
```

---

### 2. HandoffManager Integration
**File**: `core/handoff/manager.py`

**New Methods**:
```python
def create_tasks_from_decomposition(
    self, 
    parent_goal: str, 
    subtasks: List[Subtask]
) -> List[str]:
    """Add decomposed sub-tasks to ACTIVE_TASKS.md"""
    # Generate task IDs (AAS-XXX)
    # Add to task board
    # Set dependencies
    # Return task IDs

def batch_analyze_specific_tasks(
    self, 
    task_ids: List[str]
) -> str:
    """Submit specific tasks for batch analysis"""
    # Override normal queued task logic
    # Force submit these task IDs
    # Return batch ID
```

---

### 3. Batch Monitor Integration
**File**: `scripts/batch_monitor.py`

**New Hook**:
```python
async def _notify_pipeline_completion(self, batch_id: str):
    """Notify IntegrationEngine when batch completes"""
    # Check if batch belongs to a pipeline
    # If yes, trigger next stage
    # If no, process normally
```

---

### 4. Implementation Engine Integration
**File**: `core/automation/implementation_engine.py`

**New Method**:
```python
async def process_pipeline_batch(
    self, 
    batch_id: str, 
    pipeline_context: PipelineRun
) -> Dict[str, Any]:
    """Process batch within pipeline context"""
    # Standard processing
    # Add pipeline metadata to commits
    # Return detailed report for orchestrator
```

---

## Error Handling & Recovery

### Failure Scenarios

#### 1. Decomposition Fails
**Cause**: ARGO client error, API timeout, invalid goal  
**Recovery**: 
- Retry with simplified prompt
- Fall back to manual task creation
- Notify user with error details

#### 2. Batch Submission Fails
**Cause**: OpenAI API error, rate limit, invalid format  
**Recovery**:
- Retry up to 3 times with backoff
- Split into smaller batches
- Fall back to standard API if persistent failure

#### 3. Batch Timeout
**Cause**: OpenAI processing >24 hours  
**Recovery**:
- Mark batch as expired
- Re-submit tasks individually
- Notify user of delay

#### 4. Implementation Fails
**Cause**: Code generation error, validation failure, git conflict  
**Recovery**:
- Keep branch for debugging
- Mark task as "Needs Review"
- Create detailed error report
- Continue with other tasks (don't fail entire pipeline)

#### 5. Validation Fails
**Cause**: Syntax error, import error, test failure  
**Recovery**:
- Auto-fix if simple (missing import, formatting)
- Request AI re-generation for complex errors
- Fall back to manual review if auto-fix fails

---

### Rollback Mechanism

#### Automatic Rollback Triggers
1. Critical validation failure (syntax error in core/)
2. Smoke test fails (Hub won't start)
3. >50% of implementations fail validation

#### Rollback Process
```python
async def rollback_pipeline(self, pipeline_id: str):
    """Undo all changes from pipeline run"""
    # 1. Get all git branches created
    # 2. Delete branches (keep tags for debugging)
    # 3. Revert ACTIVE_TASKS.md changes
    # 4. Clear batch results
    # 5. Notify user with rollback report
```

---

## Monitoring & Observability

### Metrics to Track
```python
@dataclass
class PipelineMetrics:
    total_runs: int
    successful_runs: int
    failed_runs: int
    avg_duration: timedelta
    tasks_per_run_avg: float
    success_rate: float
    cost_per_run_avg: float
    
    # Per-stage metrics
    decompose_success_rate: float
    batch_success_rate: float
    implement_success_rate: float
    validate_success_rate: float
```

### Dashboard Integration
**File**: `dashboard/src/pages/PipelineMonitor.jsx`

**Features**:
- Real-time pipeline status
- Progress bar with current stage
- Task breakdown (created/completed)
- Error log with stack traces
- Cost tracking
- Historical runs with search/filter

---

## Configuration

### Settings in AASConfig
```python
class AutomationConfig(BaseSettings):
    # Pipeline behavior
    auto_deploy: bool = False  # Auto-merge to master
    require_approval: bool = True  # Manual approval for deployment
    max_concurrent_pipelines: int = 3
    pipeline_timeout: int = 86400  # 24 hours
    
    # Notification settings
    discord_webhook_url: Optional[SecretStr] = None
    notify_on_completion: bool = True
    notify_on_failure: bool = True
    
    # Quality gates
    require_tests: bool = False
    require_type_checks: bool = True
    min_validation_score: float = 0.8
    
    # Cost controls
    max_cost_per_pipeline: float = 10.0  # USD
    warn_at_cost: float = 5.0
```

---

## Testing Strategy

### Unit Tests
```python
# tests/test_integration_engine.py
async def test_pipeline_decompose_stage():
    """Test Stage 1: Decomposition"""
    engine = IntegrationEngine(config)
    result = await engine.run_stage("decompose", goal="Build X")
    assert result.status == "success"
    assert len(result.output) > 0  # Task IDs created

async def test_pipeline_batch_stage():
    """Test Stage 2: Batch submission"""
    # Mock HandoffManager
    # Submit batch
    # Verify batch ID returned

async def test_pipeline_error_recovery():
    """Test error handling"""
    # Simulate implementation failure
    # Verify rollback triggered
    # Check error notification sent
```

### Integration Tests
```python
async def test_full_pipeline_simple_task():
    """Test end-to-end with simple goal"""
    goal = "Create a hello world plugin"
    run = await engine.start_pipeline(goal)
    
    # Wait for completion (with timeout)
    await engine.wait_for_completion(run.id, timeout=300)
    
    # Verify plugin created
    assert Path("plugins/hello_world/__init__.py").exists()
    
    # Verify task marked done
    status = handoff_manager.get_task_status("AAS-XXX")
    assert status == "Done"
```

---

## Implementation Timeline

### Week 1: Core Orchestrator
- Day 1: Create `IntegrationEngine` class
- Day 2: Implement pipeline state machine
- Day 3: Add Stage 1-2 (Decompose, Batch)
- Day 4: Add Stage 3-4 (Wait, Implement)
- Day 5: Testing and debugging

### Week 2: Advanced Features
- Day 1: Add Stage 5-6 (Validate, Deploy)
- Day 2: Implement notification system
- Day 3: Add error recovery and rollback
- Day 4: Create monitoring dashboard
- Day 5: End-to-end testing

### Week 3: Polish & Production
- Day 1: Add configuration options
- Day 2: Performance optimization
- Day 3: Security review (secrets, git safety)
- Day 4: Documentation and examples
- Day 5: Production deployment and monitoring

---

## Success Criteria

### MVP (Minimum Viable Product)
- ✅ Can decompose simple goal into sub-tasks
- ✅ Can submit batches and wait for completion
- ✅ Can auto-implement simple plugins
- ✅ Can validate and commit changes
- ✅ Can notify user of completion

### Full Feature Set
- ✅ All 7 pipeline stages implemented
- ✅ Error recovery and rollback working
- ✅ Monitoring dashboard operational
- ✅ Cost tracking and optimization
- ✅ Linear/Discord notifications
- ✅ Multi-pipeline support
- ✅ Pause/resume capability

### Production Ready
- ✅ >90% success rate on test goals
- ✅ <5% false positive implementations
- ✅ Average pipeline time <2 hours
- ✅ Comprehensive error logging
- ✅ Security review passed
- ✅ Documentation complete

---

## Example Usage

### Command Line
```bash
# Simple goal
$ aas automate "Add dark mode to Mission Control Dashboard"

🚀 Starting automation pipeline...
📋 Stage 1: Decomposing goal into sub-tasks...
   ✅ Created 5 sub-tasks (AAS-450 to AAS-454)
📦 Stage 2: Submitting batch for analysis...
   ✅ Batch submitted: batch_abc123
⏳ Stage 3: Waiting for OpenAI to process...
   ⏱️  Estimated completion: 10-120 minutes
   ☕ Grab a coffee! You'll be notified when ready.

[2 hours later]

✅ Batch completed!
🔨 Stage 4: Implementing 5 tasks...
   ✅ AAS-450: Created plugins/dark_mode/
   ✅ AAS-451: Updated dashboard/src/theme.ts
   ✅ AAS-452: Created dashboard/src/components/ThemeToggle.jsx
   ✅ AAS-453: Updated core/config/manager.py
   ✅ AAS-454: Created tests/test_dark_mode.py
✔️ Stage 5: Validating implementations...
   ✅ All syntax checks passed
   ✅ All imports resolved
   ✅ Type checks passed (1 warning)
   ✅ 5/5 tests passed
🚀 Stage 6: Deploying...
   ✅ Created PR: "Add dark mode feature"
   ✅ Updated ACTIVE_TASKS.md
📢 Stage 7: Notifications sent!

🎉 Pipeline completed successfully!
   Duration: 2h 15m
   Tasks completed: 5
   Files created: 8
   Files modified: 3
   Cost: $0.23 (50% savings via Batch API)
   
View details: https://github.com/Aarogaming/AAS/pull/42
```

---

## Security Considerations

### Code Generation Safety
- Never execute generated code automatically
- Sandbox validation environment
- Review auto-commit messages for secrets
- Scan for common vulnerabilities (SQL injection, XSS)

### API Key Management
- Use Pydantic SecretStr for all credentials
- Never log secrets
- Rotate OpenAI API keys regularly
- Implement rate limiting to prevent cost overruns

### Git Safety
- Always work in branches
- Never force-push to master
- Require signed commits for production
- Keep rollback tags for 30 days

---

## Future Enhancements

### Self-Improvement Loop
- Analyze successful implementations
- Fine-tune prompts based on outcomes
- Build library of reusable patterns
- A/B test different decomposition strategies

### Multi-Agent Collaboration
- Assign sub-tasks to specialized agents (Sixth, ChatGPT, Claude)
- Implement voting/consensus for complex decisions
- Red-team generated code for security

### Advanced Optimization
- Predict implementation time based on complexity
- Optimize batch grouping for faster completion
- Cache common patterns to skip generation
- Parallelize independent implementations

---

## Dependencies

### Required Before Starting
- ✅ AAS-227 (Implementation Engine) - MVP complete
- ⚠️ AAS-211 (Task Decomposition) - In progress, not blocking

### Optional Enhancements
- Linear API integration for enterprise sync
- Discord bot for team notifications
- Prometheus metrics for monitoring
- Grafana dashboard for visualization

---

## Questions for Implementer

1. **Should pipelines run sequentially or in parallel?**
   - Recommendation: Parallel with max_concurrent limit (3)

2. **How to handle user intervention during pipeline?**
   - Recommendation: Pause/resume capability, save state to DB

3. **Should we auto-merge to master?**
   - Recommendation: Create PR by default, auto-merge only if configured

4. **How to prioritize multiple pipelines?**
   - Recommendation: FIFO queue, support priority overrides

5. **What to do if a pipeline runs for >24 hours?**
   - Recommendation: Timeout and notify, allow manual resume

---

**Status**: Ready for implementation  
**Assignee**: TBD (queued, blocked by AAS-227)  
**Estimated Effort**: 2-3 weeks for full system, 1 week for MVP  
**Blockers**: AAS-227 (Implementation Engine) must be complete first

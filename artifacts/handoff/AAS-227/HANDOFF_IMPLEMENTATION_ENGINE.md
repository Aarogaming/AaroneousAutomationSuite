# Handoff Document: AAS-227 - Automated Implementation Engine

**Task ID**: AAS-227  
**Priority**: High  
**Status**: Queued  
**Created**: 2026-01-03  
**Dependencies**: AAS-211 (Task Decomposition - In Progress)

---

## Executive Summary

Build an automated implementation engine that converts OpenAI Batch API analysis results into working code files without manual intervention. This is the **critical missing piece** for full automation - we can submit batches and retrieve results, but cannot yet apply them automatically.

**Expected Impact**:
- **95% time savings** (4 hours → 10 minutes per task)
- **50% cost savings** (already using Batch API)
- **3x throughput** (2-3 tasks/day → 20+ tasks/day)
- **Lower error rate** (20% → 5% with validation layer)

---

## Current State Analysis

### ✅ What's Working
1. **Batch Submission**: `scripts/batch_monitor.py`
   - Scans ACTIVE_TASKS.md every 60 seconds
   - Auto-submits queued tasks to OpenAI Batch API
   - Tracks state in `artifacts/batch/monitor_state.json`
   - Running continuously in background

2. **Batch Retrieval**: `scripts/retrieve_both_batches.py`
   - Downloads completed batch results
   - Parses JSON responses
   - Saves to `artifacts/batch/results/*.json`

3. **Analysis Results**: 2 batches completed (9 tasks analyzed)
   - Batch 1: `batch_6959bf81f4588190ba2f533dffd5005e` (6 tasks)
   - Batch 2: `batch_6959c7f462008190ac8888fda6d28d7c` (3 tasks)
   - All include: complexity estimates, priority recommendations, blockers, first steps
   - Saved analysis report: `artifacts/batch/reports/BATCH_ANALYSIS_2026-01-03.md`

### ❌ What's Missing (This Task)
**No automatic code generation from batch results**

Current `scripts/batch_implementer.py`:
- Only extracts code blocks from AI responses
- Cannot map analysis to file structure
- Requires manual file creation
- No validation or testing

**Gap**: Analysis sits in JSON files, never becomes actual code

---

## Technical Context

### Existing Infrastructure

#### 1. Batch Results Format
```json
{
  "batch_id": "batch_6959c7f462008190ac8888fda6d28d7c",
  "results": [
    {
      "custom_id": "AAS-224",
      "response": {
        "body": {
          "choices": [{
            "message": {
              "content": "1. **Estimated Complexity**: High\n2. **Recommended Priority**: Medium\n3. **Potential Blockers**: Payment integration, user system\n4. **First Step**: Requirements gathering session\n\nImplementation Plan:\nPhase 1: Design plugin manifest (aas-plugin.json)\nPhase 2: Build registry backend...\n"
            }
          }]
        }
      }
    }
  ]
}
```

#### 2. Target File Structure
Based on successful implementations (AAS-109 Penpot, AAS-110 DevToys, AAS-112 ngrok):
```
plugins/<plugin_name>/
├── __init__.py              # PluginBase registration
├── <plugin_name>_plugin.py  # Main plugin class
├── config.py                # Pydantic configuration
└── [additional modules]     # Service classes, adapters, etc.

core/services/
└── <service_name>.py        # Standalone services (like ngrok)

core/config/manager.py       # Add new config fields here
```

#### 3. Plugin Template Pattern
```python
# plugins/example/example_plugin.py
from core.plugin_base import PluginBase
from .config import ExampleConfig

class ExamplePlugin(PluginBase):
    def __init__(self, config: ExampleConfig):
        super().__init__(name="example", version="1.0.0")
        self.config = config
    
    async def initialize(self):
        logger.info(f"Initializing {self.name}")
        # Setup logic
    
    async def cleanup(self):
        logger.info(f"Cleaning up {self.name}")
        # Teardown logic

def register(hub):
    config = ExampleConfig()
    plugin = ExamplePlugin(config)
    hub.register_plugin(plugin)
```

---

## Implementation Plan

### Architecture

```
core/automation/
├── implementation_engine.py    # Main orchestrator (ImplementationEngine class)
├── code_generator.py          # Code generation logic (CodeGenerator class)
├── file_applier.py            # Safe file operations (FileApplier class)
├── validation.py              # Pre/post checks (Validator class)
└── templates/                 # Jinja2 templates for boilerplate
    ├── plugin_init.py.j2
    ├── plugin_main.py.j2
    ├── plugin_config.py.j2
    └── service.py.j2
```

### Component Details

#### 1. ImplementationEngine (Orchestrator)
**File**: `core/automation/implementation_engine.py`

**Responsibilities**:
- Load batch results from `artifacts/batch/results/`
- Parse AI analysis into structured implementation plan
- Coordinate code generation, file application, validation
- Update ACTIVE_TASKS.md status
- Handle errors and rollbacks

**Key Methods**:
```python
class ImplementationEngine:
    async def process_batch(self, batch_id: str) -> Dict[str, Any]:
        """Process all tasks in a completed batch"""
        # 1. Load batch results
        # 2. For each task: parse_analysis() → generate_code() → apply_files()
        # 3. Validate implementation
        # 4. Update task status
        # 5. Return summary report
    
    def parse_analysis(self, task_id: str, ai_response: str) -> ImplementationPlan:
        """Convert AI text into structured plan"""
        # Extract: complexity, phases, file specs, dependencies
        # Map to plugin/service/core structure
    
    async def apply_implementation(self, plan: ImplementationPlan) -> bool:
        """Execute implementation plan safely"""
        # 1. Create git branch
        # 2. Generate code from templates
        # 3. Apply files
        # 4. Run validation
        # 5. Commit if success, rollback if failure
```

#### 2. CodeGenerator (Template Engine)
**File**: `core/automation/code_generator.py`

**Responsibilities**:
- Use Jinja2 to generate boilerplate code
- Smart import detection and resolution
- Type hint generation
- Docstring generation (Google style)

**Key Methods**:
```python
class CodeGenerator:
    def generate_plugin(self, spec: PluginSpec) -> Dict[str, str]:
        """Generate all files for a plugin"""
        # Returns: {filepath: content}
    
    def generate_config_class(self, spec: ConfigSpec) -> str:
        """Generate Pydantic config class"""
    
    def add_to_config_manager(self, fields: List[ConfigField]) -> str:
        """Generate config additions for manager.py"""
```

#### 3. FileApplier (Safe File Operations)
**File**: `core/automation/file_applier.py`

**Responsibilities**:
- Create files/directories safely
- Update existing files (via AST parsing for Python)
- Git integration (branch, commit, rollback)
- Backup before modifications

**Key Methods**:
```python
class FileApplier:
    async def create_file(self, path: Path, content: str) -> bool:
        """Create new file with backup"""
    
    async def update_file(self, path: Path, changes: Dict) -> bool:
        """Safely modify existing file"""
        # Use AST for Python files
        # Use regex/string replacement for others
    
    async def create_branch(self, name: str) -> bool:
        """Create git branch for implementation"""
    
    async def commit_changes(self, message: str) -> bool:
        """Commit with structured message"""
```

#### 4. Validator (Quality Assurance)
**File**: `core/automation/validation.py`

**Responsibilities**:
- Syntax checking (compile test)
- Import resolution
- Type checking (mypy)
- Test execution (if tests exist)
- Integration smoke test

**Key Methods**:
```python
class Validator:
    def validate_syntax(self, filepath: Path) -> ValidationResult:
        """Check Python syntax via ast.parse()"""
    
    def validate_imports(self, filepath: Path) -> ValidationResult:
        """Verify all imports are resolvable"""
    
    def validate_types(self, filepath: Path) -> ValidationResult:
        """Run mypy on file"""
    
    async def smoke_test(self, plugin_name: str) -> ValidationResult:
        """Try loading plugin in test environment"""
```

---

## Implementation Phases

### Phase 1: Core Engine (Day 1)
**Goal**: Basic orchestrator that can process batch results

**Tasks**:
1. Create `ImplementationEngine` class
2. Implement `parse_analysis()` - extract structured data from AI text
3. Implement `process_batch()` - coordinate workflow
4. Test with AAS-224 analysis (Community Forge)

**Validation**: Can parse batch results into implementation plans

---

### Phase 2: Code Generation (Day 2)
**Goal**: Generate working plugin boilerplate

**Tasks**:
1. Create Jinja2 templates for plugin structure
2. Implement `CodeGenerator` class
3. Add smart import detection
4. Test with AAS-014 (DanceBot) - compare against `Wizard101_DanceBot/`

**Validation**: Generated code matches hand-written structure

---

### Phase 3: File Application (Day 3)
**Goal**: Safely apply generated code to workspace

**Tasks**:
1. Implement `FileApplier` with git integration
2. Add backup/rollback mechanism
3. Implement AST-based updates for Python files
4. Test creating new plugin end-to-end

**Validation**: Can create working plugin from scratch

---

### Phase 4: Validation & Integration (Day 4)
**Goal**: Ensure generated code quality and integrate with monitor

**Tasks**:
1. Implement `Validator` class with all checks
2. Integrate with `batch_monitor.py`
3. Add auto-update of ACTIVE_TASKS.md
4. End-to-end test: submit batch → auto-implement

**Validation**: Full automation loop works without manual intervention

---

## Data Structures

### ImplementationPlan
```python
@dataclass
class ImplementationPlan:
    task_id: str
    complexity: str  # Low/Medium/High
    priority: str    # Low/Medium/High
    blockers: List[str]
    phases: List[Phase]
    files: List[FileSpec]
    config_additions: List[ConfigField]
    dependencies: List[str]  # Other task IDs

@dataclass
class Phase:
    number: int
    title: str
    description: str
    tasks: List[str]

@dataclass
class FileSpec:
    path: Path
    type: str  # "plugin", "service", "config", "test"
    template: str  # Template name
    variables: Dict[str, Any]  # Template variables

@dataclass
class ConfigField:
    name: str
    type: str
    default: Any
    description: str
    secret: bool = False
```

---

## Integration Points

### 1. Batch Monitor Integration
**File**: `scripts/batch_monitor.py`

**Change**:
```python
async def _process_batch_results(self, batch_id: str, metadata: Dict):
    """Process completed batch results"""
    # Existing retrieval logic...
    
    # NEW: Auto-implement
    from core.automation.implementation_engine import ImplementationEngine
    engine = ImplementationEngine(self.config)
    
    try:
        report = await engine.process_batch(batch_id)
        logger.success(f"Auto-implemented {report['success_count']} tasks")
        
        # Update Linear if configured
        if self.linear_client:
            await self._sync_to_linear(report)
    except Exception as e:
        logger.error(f"Auto-implementation failed: {e}")
        # Fall back to manual review
```

### 2. HandoffManager Integration
**File**: `core/handoff/manager.py`

**New Method**:
```python
def mark_implemented(self, task_id: str, implementation_summary: str):
    """Mark task as Done after successful implementation"""
    lines, tasks, status_map = self.parse_board()
    
    # Update status to Done
    # Add implementation notes
    # Update timestamp
    
    self._write_board(updated_lines)
    logger.success(f"Marked {task_id} as Done")
```

---

## Test Cases

### Test 1: Parse Analysis
**Input**: Batch result JSON for AAS-224  
**Expected**: ImplementationPlan with 4 phases, 8 files  
**Validates**: Analysis parsing logic

### Test 2: Generate Plugin
**Input**: PluginSpec for "community_forge"  
**Expected**: Valid Python files matching template  
**Validates**: Code generation

### Test 3: Apply Files
**Input**: Generated files for test plugin  
**Expected**: Files created, git committed  
**Validates**: File application safety

### Test 4: Validate Code
**Input**: Generated plugin code  
**Expected**: Pass syntax, import, type checks  
**Validates**: Quality assurance

### Test 5: End-to-End
**Input**: Batch ID for AAS-014 (DanceBot)  
**Expected**: Working plugin in `plugins/dance_bot/`  
**Validates**: Full automation pipeline

---

## Success Metrics

### Quantitative
- **Processing Speed**: <10 minutes per task (vs 2-4 hours manual)
- **Success Rate**: >90% of generated code passes validation
- **Error Rate**: <5% of implementations need manual fixes
- **Throughput**: 20+ tasks/day (vs 2-3 manual)

### Qualitative
- Generated code follows AAS conventions (PluginBase, Pydantic configs)
- Proper error handling and logging
- Type hints and docstrings present
- Passes existing code quality standards

---

## Risk Assessment

### High Risk
1. **AI output parsing variability**
   - **Mitigation**: Use structured prompts in batch requests, add fallback parsers

2. **Breaking existing code**
   - **Mitigation**: Git branching, backups, rollback on validation failure

3. **Complex refactoring tasks**
   - **Mitigation**: Start with new plugin creation, add update logic later

### Medium Risk
1. **Template maintenance**
   - **Mitigation**: Version templates, keep simple initially

2. **Import resolution failures**
   - **Mitigation**: Whitelist common imports, auto-install missing packages

### Low Risk
1. **Git conflicts**
   - **Mitigation**: Always create new branch, fail gracefully on conflicts

---

## References

### Existing Implementations (Study These)
1. **plugins/penpot/** - Full async plugin (AAS-109)
2. **plugins/devtoys/** - Task execution pattern (AAS-110)
3. **core/services/ngrok.py** - Service-style implementation (AAS-112)

### Related Code
- `scripts/batch_implementer.py` - Prototype code extractor
- `scripts/batch_recycler.py` - Result parsing utilities
- `core/handoff/agents/argo_client.py` - Task decomposition (for Phase 2)

### Documentation
- `docs/AUTOMATION_ROADMAP.md` - Full automation strategy
- `artifacts/batch/reports/BATCH_ANALYSIS_2026-01-03.md` - Latest batch analysis
- `.github/copilot-instructions.md` - AAS development conventions

---

## Next Steps

1. **Immediate**: Create task in ACTIVE_TASKS.md as "Queued"
2. **Phase 1**: Implement ImplementationEngine.parse_analysis()
3. **Test Early**: Use AAS-224 analysis as first test case
4. **Iterate**: Start simple (plugin creation only), add complexity incrementally

---

## Questions for Implementer

1. Should we use OpenAI for code generation or rely on templates?
   - **Recommendation**: Templates for structure, GPT-4 for business logic

2. How to handle dependencies between generated files?
   - **Recommendation**: Topological sort, apply base files first

3. What to do if validation fails?
   - **Recommendation**: Keep branch, create issue in ACTIVE_TASKS.md for manual fix

4. Should we auto-merge to master or require PR review?
   - **Recommendation**: Auto-commit to branch, manual merge initially

---

**Status**: Ready for implementation  
**Assignee**: TBD (queued)  
**Estimated Effort**: 3-4 days for full implementation, 1-2 days for MVP  
**Blockers**: None (AAS-211 in progress but not required to start)

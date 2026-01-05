# Roadmap Integration with TaskGenerator

**Created**: January 4, 2026  
**Status**: ✅ Implemented  
**Feature**: Automated task generation from roadmap documents

---

## Overview

The TaskGenerator now parses roadmap markdown files to extract unchecked tasks and automatically suggest them when the task backlog is low. This creates a feedback loop between strategic planning (roadmaps) and tactical execution (Linear tasks).

## Implementation

### Files Modified
- [core/batch/task_generator.py](../core/batch/task_generator.py) - Added roadmap parsing logic

### New Methods

#### `parse_roadmap(roadmap_path: Path) -> List[Dict[str, Any]]`

Parses a roadmap markdown file and extracts unchecked tasks using these patterns:
- `- [ ] Task description` - Unchecked markdown checkbox
- `- [ ] **AAS-XXX**: Task with ID` - Tasks with Linear IDs

**Features**:
- Tracks current phase/section context for better task descriptions
- Extracts task IDs if present (e.g., `AAS-211`)
- Infers priority from keywords (urgent, high priority, critical, etc.)
- Includes contextual information (phase, section) in task description
- Looks ahead for additional context (next 3 lines)

**Example Output**:
```python
{
    'title': 'Automated Task Decomposition',
    'description': 'Automated Task Decomposition\n\nContext: Phase 2: Automation & Integration → Week 1-2',
    'priority': 'medium',
    'phase': 'Phase 2: Automation & Integration (Q1 - Q2 2026)',
    'section': 'Week 1-2: Automated Implementation Engine',
    'task_id': 'AAS-211',
    'source': 'roadmap:MASTER_ROADMAP',
    'type': 'feature',
    'auto_generated': True
}
```

### Modified Methods

#### `review_project_progress()`

Now includes roadmap analysis:

1. **Low Backlog Scenario** (< 5 tasks):
   - Parses all roadmap files
   - Extracts top 5 priority tasks
   - Adds them to suggestions automatically

2. **High Roadmap Count** (> 20 unchecked tasks):
   - Creates a planning task to review roadmap items
   - Includes top 5 priorities in description

### Supported Roadmaps

The TaskGenerator monitors these files:
- `docs/MASTER_ROADMAP.md`
- `docs/AUTOMATION_ROADMAP.md`
- `docs/DESKTOP_GUI_ROADMAP.md`
- `docs/GAME_AUTOMATION_ROADMAP.md`

## Test Results

**Tested**: January 4, 2026  
**Test Script**: [scripts/test_roadmap_parsing.py](../scripts/test_roadmap_parsing.py)

### Results Summary

| Roadmap | Unchecked Tasks |
|---------|-----------------|
| MASTER_ROADMAP.md | 84 |
| AUTOMATION_ROADMAP.md | 0 |
| DESKTOP_GUI_ROADMAP.md | 56 |
| GAME_AUTOMATION_ROADMAP.md | 95 |
| **TOTAL** | **235** |

### Priority Breakdown (All Roadmaps)
- **Urgent**: 1 task
- **High**: 1 task
- **Medium**: 232 tasks
- **Low**: 1 task

### Top 5 Priority Tasks Extracted
1. [URGENT] Safety: Zero critical errors in 100 test episodes (Game Learning)
2. [HIGH] Log all corrections as high-value training data (Ghost Mode)
3. [MEDIUM] Automated Task Decomposition (AAS-211)
4. [MEDIUM] Parse batch results → structured implementation plans
5. [MEDIUM] Generate code files from analysis

## Usage

### Manual Testing
```bash
# Activate virtual environment
.venv\Scripts\Activate.ps1

# Run test script
python scripts/test_roadmap_parsing.py
```

### Automatic Operation

The TaskGenerator runs automatically via:
- `scripts/batch_monitor.py` - Periodic task review
- `core/main.py` - CLI command: `python core/main.py generate-tasks`

When task backlog drops below 5:
1. TaskGenerator parses all roadmaps
2. Extracts unchecked `- [ ]` items
3. Sorts by priority (urgent → high → medium → low)
4. Creates Linear issues for top 5 tasks

## Benefits

### Strategic Alignment
- Tasks are automatically sourced from documented strategic plans
- No need to manually transcribe roadmap items into Linear

### Reduced Manual Work
- Automated task creation when backlog is low
- Ensures continuous work pipeline

### Context Preservation
- Tasks include phase and section context
- Links back to source roadmap
- Maintains strategic narrative

### Visibility
- See which roadmap items are pending (235 across all roadmaps)
- Prioritize based on urgency keywords in roadmap text

## Configuration

### Adding New Roadmaps

Edit [task_generator.py](../core/batch/task_generator.py):

```python
self.roadmap_files = [
    Path("docs/MASTER_ROADMAP.md"),
    Path("docs/YOUR_NEW_ROADMAP.md"),  # Add here
]
```

### Adjusting Priority Detection

Modify keywords in `parse_roadmap()`:

```python
# Urgent priority keywords
if any(word in text_lower for word in ['critical', 'urgent', 'high priority']):
    priority = 'urgent'
```

### Changing Threshold

Adjust when roadmap tasks are suggested:

```python
# Currently: < 5 tasks triggers roadmap scan
if task_stats['queued'] + task_stats['todo'] < 5:
```

## Future Enhancements

### Planned Improvements
- [ ] Query AnythingLLM for roadmap context when generating task descriptions
- [ ] Use TaskDecomposer (LangGraph) to break roadmap phases into subtasks
- [ ] Add roadmap completion percentage to dashboard
- [ ] Track which roadmap items have been implemented
- [ ] Auto-check `- [x]` items in roadmap when Linear task completes

### Integration Ideas
- [ ] Weekly roadmap review report (% complete per phase)
- [ ] Notify when critical roadmap items are blocked
- [ ] Suggest re-prioritization based on roadmap vs actual progress
- [ ] Auto-update roadmap dates based on task velocity

## Examples

### Scenario 1: Low Task Backlog

**State**: 3 tasks in queue  
**Action**: TaskGenerator runs `review_project_progress()`  
**Result**:
```
✓ Parsed 235 unchecked tasks from roadmaps
✓ Created 5 Linear issues:
  - AAS-XXX: Automated Task Decomposition
  - AAS-XXX: Parse batch results
  - AAS-XXX: Generate code files
  - AAS-XXX: Technology decision document (Desktop GUI)
  - AAS-XXX: Extend StateActionRecorder (Game Learning)
```

### Scenario 2: Many Pending Roadmap Items

**State**: 235 unchecked roadmap tasks  
**Action**: TaskGenerator detects high roadmap count  
**Result**:
```
✓ Created planning task:
  "Review 235 Pending Roadmap Items"
  Description includes top 5 priorities for quick review
```

## See Also

- [MASTER_ROADMAP.md](MASTER_ROADMAP.md) - Unified strategic timeline
- [AUTOMATION_ROADMAP.md](AUTOMATION_ROADMAP.md) - Batch processing plan
- [DESKTOP_GUI_ROADMAP.md](DESKTOP_GUI_ROADMAP.md) - Desktop app plan
- [GAME_AUTOMATION_ROADMAP.md](GAME_AUTOMATION_ROADMAP.md) - ML/RL learning plan
- [TASK_MANAGER_GUIDE.md](TASK_MANAGER_GUIDE.md) - Task management overview

---

**Status**: Fully operational and tested ✅

# "Leave It Better Than You Found It" Policy Evaluation

## Executive Summary

**Recommendation**: **Adopt with guardrails** - Implement a tiered "Leave It Better" policy with clear scope boundaries to prevent scope creep while encouraging incremental improvements.

**Key Finding**: AAS has a **healthy baseline** (minimal technical debt markers, consistent patterns) but **organizational inconsistencies** (15 test files in `scripts/` vs `tests/`, varied import patterns) that would benefit from standardized improvement triggers.

**Impact Assessment**:
- ✅ **Benefits**: 80% reduction in boilerplate (ManagerHub), consistent patterns, reduced onboarding friction
- ⚠️ **Risks**: PR scope creep, increased review time, "improvement paralysis"
- 🎯 **Mitigation**: Clear triggers, 5-minute rule, automated checks

---

## Current State Analysis

### Code Quality Baseline (as of 2026-01-02)

**Technical Debt Audit**:
```
TODO/FIXME markers:     20 matches (mostly debug logging, not actual debt)
Type errors:            7 in migrate_tasks_to_db.py (SQLAlchemy ORM mismatches)
Lint errors:            496 markdown formatting issues (MD022, MD032, MD009)
Import patterns:        30 scripts using sys.path.insert boilerplate
Test organization:      15 test_*.py in scripts/, 1 in tests/ directory
Missing docstrings:     15+ functions with no docstring (functions ending with :$)
```

**Health Indicators**:
- ✅ **Low critical debt**: No HACK/XXX/BUG markers found
- ✅ **Consistent logging**: Loguru used throughout
- ⚠️ **Type safety gaps**: SQLAlchemy ORM assignment errors
- ⚠️ **Inconsistent imports**: Every script reinvents path setup
- ⚠️ **Documentation gaps**: Many functions lack docstrings

### Improvement Opportunity Matrix

| Area | Current Pain Level | Effort to Fix | ROI | Priority |
|------|-------------------|---------------|-----|----------|
| Manager init boilerplate | 🔴 High (10-15 lines) | Low (2 days) | 🟢 High (80% reduction) | **P0** |
| Import patterns | 🟡 Medium | Low (1 day) | 🟢 High (eliminates 5 lines/script) | **P0** |
| Test organization | 🟡 Medium | Medium (3 days) | 🟡 Medium | **P1** |
| Markdown linting | 🟡 Medium | Low (1 day) | 🟡 Medium | **P2** |
| Type errors | 🟡 Medium | Medium (2 days) | 🟢 High (prevents bugs) | **P1** |
| Missing docstrings | 🟢 Low | High (ongoing) | 🟡 Medium | **P3** |

---

## Policy Framework

### Core Principle

> **"When you touch a file, make one small improvement beyond your immediate task—but only if it takes ≤5 minutes."**

### The 5-Minute Rule

**Do this**:
- Add a missing docstring to a function you're editing
- Fix obvious typos or formatting in code you're reading
- Use ManagerHub if creating a new script
- Move a test file from `scripts/` to `tests/` if you're already editing it
- Add a type hint to a function parameter you're using

**Don't do this**:
- Refactor an entire module because you edited one function
- Rewrite tests for a file you're not testing
- Convert all scripts to ManagerHub in one PR
- Fix every lint error in a file you touched

### Improvement Tiers

#### Tier 1: **Mandatory** (Zero Extra Effort)
These improvements are **required** when touching code:
- **Use ManagerHub for new scripts** - If creating a script, start with `ManagerHub.create()`
- **Place tests in tests/** - No new test files in `scripts/` directory
- **Fix type errors you create** - Don't introduce new type checker warnings
- **No secrets in code** - Use `.env` for any API keys

#### Tier 2: **Encouraged** (5-Minute Rule)
These improvements are **encouraged** if quick:
- **Add missing docstrings** - To functions you're editing
- **Fix obvious lint errors** - In sections you're changing
- **Convert old manager init** - If editing a script's setup section
- **Add type hints** - To parameters you're using

#### Tier 3: **Opportunistic** (10-Minute Rule)
These improvements are **nice-to-have** if time permits:
- **Consolidate imports** - If editing import section
- **Extract magic numbers** - If changing related logic
- **Add logging** - To error paths you're modifying
- **Update stale comments** - If understanding the code

#### Tier 4: **Planned** (Separate PR)
These improvements **require dedicated work**:
- **Migrate existing scripts to ManagerHub** - Coordinate via task board
- **Refactor large modules** - Needs design review
- **Add missing test coverage** - Dedicated testing sprint
- **Fix all markdown lint errors** - Bulk cleanup task

---

## Specific Triggers

### When Creating a New Script

**Required Changes**:
```python
# ❌ OLD (Don't write this)
import sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).parent.parent))
from core.config import load_config
from core.handoff_manager import HandoffManager
config = load_config()
handoff = HandoffManager(config=config)

# ✅ NEW (Write this)
from core.managers import ManagerHub
hub = ManagerHub.create()
```

**Rationale**: New code should use new patterns from day one.

---

### When Editing Existing Scripts

**Encouraged Changes** (if already editing imports):
```python
# ❌ OLD (Don't change unless editing imports)
import sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).parent.parent))
from core.config import load_config

# ✅ NEW (If you're already modifying the import section)
from core.managers import ManagerHub
hub = ManagerHub.create()
```

**Rationale**: Don't refactor just for refactoring's sake, but if you're already there, upgrade.

---

### When Adding a Function

**Required**:
```python
# ❌ Missing docstring
def calculate_priority(task):
    return task.priority * 2

# ✅ Added docstring (30 seconds of effort)
def calculate_priority(task):
    """Calculate adjusted priority for task scheduling.
    
    Args:
        task: Task object with priority attribute
        
    Returns:
        Doubled priority value for urgent weighting
    """
    return task.priority * 2
```

**Rationale**: Documentation at creation time prevents technical debt.

---

### When Fixing a Bug

**Encouraged**:
```python
# ❌ Fix bug but leave poor naming
def calc(t):
    return t.p * 2 if t.p else 0

# ✅ Fix bug AND improve clarity (1 minute extra)
def calculate_adjusted_priority(task):
    """Calculate priority with fallback for None values."""
    return task.priority * 2 if task.priority else 0
```

**Rationale**: Bugs often occur in poorly named/documented code. Fix both.

---

### When Creating a Test

**Required**:
```bash
# ❌ Wrong location
scripts/test_new_feature.py

# ✅ Correct location
tests/test_new_feature.py
```

**Rationale**: Standardize test discovery and organization.

---

### When You See Type Errors

**Required** (if you introduced them):
```python
# ❌ Introduces type error
task.priority = "high"  # Column[str] expects str, not literal

# ✅ Fixed type error
task.priority = TaskPriority.HIGH.value  # Correctly typed
```

**Encouraged** (if you're already there):
```python
# Fix nearby type errors in the same function (if < 5 minutes)
```

**Rationale**: Don't leave the codebase worse than you found it.

---

## Enforcement Mechanisms

### Automated Checks (CI/CD)

**Pre-commit Hooks** (planned):
```bash
# Block commits with:
- API keys in code (detect via regex)
- New files in scripts/test_*.py pattern
- Type errors in changed files (mypy --files changed)
- Missing docstrings on new functions (interrogate)
```

**PR Checks**:
```bash
# Warn (but don't block) for:
- Scripts not using ManagerHub
- Missing type hints on new functions
- Markdown lint errors in docs/
```

### Code Review Guidelines

**Reviewers should ask**:
1. "Does this PR introduce new technical debt?"
2. "If touching imports, did they use ManagerHub?"
3. "Are new functions documented?"
4. "Did they fix obvious issues they encountered?"

**Reviewers should NOT ask**:
1. "Why didn't you refactor this entire module?"
2. "Can you convert all old scripts to ManagerHub?"
3. "Please fix all lint errors in the repo"

### Scope Creep Prevention

**PR size limits** (suggested):
- 🟢 **Small**: 1-3 files, <200 lines changed
- 🟡 **Medium**: 4-8 files, 200-500 lines changed
- 🔴 **Large**: 9+ files, 500+ lines changed

**If a PR grows too large**:
1. Split improvements into separate "cleanup" PR
2. Use task board for larger refactoring (e.g., "AAS-114: Migrate all scripts to ManagerHub")
3. Mark improvements as follow-up tasks

---

## Metrics for Success

### Short-Term (1 month)
- ✅ 100% of new scripts use ManagerHub
- ✅ 0 new test files in `scripts/` directory
- ✅ <5 type errors in new code (measured by mypy)
- ✅ >80% of new functions have docstrings

### Medium-Term (3 months)
- ✅ >50% of scripts migrated to ManagerHub (gradual)
- ✅ All tests in `tests/` directory
- ✅ Markdown lint errors <100 (from 496)
- ✅ Type error count trending down

### Long-Term (6 months)
- ✅ 100% ManagerHub adoption
- ✅ 0 lint errors in critical files
- ✅ >90% function docstring coverage
- ✅ Type safety at >95% coverage

---

## Integration with Manager Improvements

### Phase 1 Synergy (Foundation)

The "Leave It Better" policy **accelerates** ManagerHub adoption:

**Without policy**: 
- "We built ManagerHub, now let's wait for people to adopt it"
- Adoption rate: ~10% (only new scripts)

**With policy**:
- "When touching a script, use ManagerHub if editing imports"
- Adoption rate: ~50-70% (gradual migration)

### Phase 2-4 Considerations

**Phase 2 (DX Improvements)**:
- Tiered config → Encourage splitting `AASConfig` when adding new fields
- Guided errors → Add to existing error handlers (5-minute rule)

**Phase 3 (Documentation)**:
- When editing a function, add docstring (mandatory)
- When fixing a bug, update relevant docs (encouraged)

**Phase 4 (Web Dashboard)**:
- New feature, no policy impact (greenfield)

---

## Risk Mitigation

### Risk 1: **Scope Creep**
**Symptom**: PRs balloon from "fix bug" to "refactor entire module"

**Mitigation**:
- Enforce 5-minute rule in code reviews
- Split large PRs into feature + cleanup
- Use task board for planned refactoring

### Risk 2: **Improvement Paralysis**
**Symptom**: Developers spend more time thinking about improvements than fixing bugs

**Mitigation**:
- Clear tier system (mandatory vs. encouraged)
- "When in doubt, skip it" - improvements are never required beyond Tier 1

### Risk 3: **Inconsistent Enforcement**
**Symptom**: Some PRs held to high standards, others rubber-stamped

**Mitigation**:
- Automated checks for Tier 1 violations (block CI)
- Reviewer checklist in PR template
- Regular retros on policy effectiveness

### Risk 4: **Technical Debt Theater**
**Symptom**: Cosmetic improvements (renaming) without addressing root causes

**Mitigation**:
- Focus on high-ROI improvements (ManagerHub, type safety)
- Track metrics (type error count, test coverage)
- Celebrate substantive improvements in team meetings

---

## Real-World Examples

### Example 1: Bug Fix in `core/main.py`

**Scenario**: Fix a crash when task has no priority

**Minimum PR** (acceptable):
```python
# Fix the crash
priority = task.priority if task.priority else "medium"
```

**Better PR** (encouraged):
```python
def get_task_priority(task: Task) -> str:
    """Extract priority with fallback to medium.
    
    Args:
        task: Task object to extract priority from
        
    Returns:
        Priority string ("urgent", "high", "medium", "low")
    """
    return task.priority if task.priority else "medium"

# Usage
priority = get_task_priority(task)
```

**Time investment**: +2 minutes for docstring + type hints
**Benefit**: Reusable function, self-documenting code

---

### Example 2: Adding a CLI Command

**Scenario**: Add `task archive` command to `scripts/task_manager_cli.py`

**Minimum PR** (if file already uses old pattern):
```python
# Just add the command
def archive_task(task_id):
    # ... implementation
```

**Better PR** (if this were a new script):
```python
# New script → use ManagerHub from the start
from core.managers import ManagerHub

@click.command()
def archive(task_id):
    """Archive a completed task."""
    hub = ManagerHub.create()
    # ... implementation
```

**Decision**: Since `task_manager_cli.py` already uses old pattern, don't refactor entire file. But if creating `scripts/aas_cli.py` (new file), use ManagerHub.

---

### Example 3: Lint Errors in Documentation

**Scenario**: Editing `docs/MANAGER_IMPROVEMENTS.md`, notice 496 lint errors in `docs/`

**Minimum PR** (acceptable):
```markdown
# Fix lint errors in the file you're editing
- Added blank lines around headings
- Fixed trailing spaces
```

**Better PR** (if quick):
```markdown
# Fix lint errors in MANAGER_IMPROVEMENTS.md + nearby files
- Fixed all MD022 errors in docs/MANAGER_*.md (5 files)
- Consistent formatting across manager docs
```

**Time investment**: +5 minutes to fix nearby files
**Don't do**: Fix all 496 lint errors across 20 files (separate task)

---

## Policy Evolution

### Quarterly Review

Every 3 months, review:
1. **Adoption metrics** - Are new scripts using ManagerHub?
2. **PR velocity** - Is review time increasing?
3. **Technical debt trends** - Type errors, lint errors, test coverage
4. **Developer feedback** - Is policy helping or hindering?

### Adjustment Criteria

**Tighten policy** (move Tier 2 → Tier 1) if:
- ✅ Adoption rate is high (>80% compliance)
- ✅ Improvements are quick and easy (< 3 minutes average)
- ✅ ROI is proven (measurable reduction in bugs)

**Loosen policy** (move Tier 1 → Tier 2) if:
- ❌ PRs taking significantly longer to review
- ❌ Developers expressing frustration
- ❌ No measurable improvement in code quality

---

## FAQ

### Q: "What if I'm fixing a critical bug and don't have time for improvements?"
**A**: Fix the bug. Critical fixes are exempt from all non-mandatory improvements (Tier 1 still applies).

### Q: "What if the 'obvious improvement' would take 15 minutes?"
**A**: Skip it or create a follow-up task. The 5-minute rule is a guideline, not a mandate.

### Q: "What if my PR reviewer asks for improvements I don't think are necessary?"
**A**: Discuss in PR comments. Reviewer should reference this policy to justify requests. If disagreement persists, escalate to team lead.

### Q: "Can I batch improvements into a separate 'cleanup PR'?"
**A**: Yes! This is encouraged. Keep feature work and cleanup work separate if the cleanup is substantial (>5 minutes).

### Q: "What if I don't know how to make the improvement?"
**A**: Ask in PR comments or team chat. Improvements should never block progress. If unsure, skip it.

---

## Conclusion

### Adopt with Guardrails

The "Leave It Better" policy is **beneficial** for AAS because:
1. **ManagerHub adoption** - Accelerates migration to new patterns
2. **Incremental cleanup** - Prevents technical debt accumulation
3. **Learning culture** - Encourages knowledge sharing

But requires **guardrails**:
1. **5-minute rule** - Prevents scope creep
2. **Tiered system** - Clear mandatory vs. encouraged boundaries
3. **Automated checks** - Enforces critical rules without manual review burden

### Next Steps

1. **Approve policy** - Get team consensus on tiers and rules
2. **Add to docs** - Update CONTRIBUTING.md with policy summary
3. **Set up pre-commit hooks** - Block Tier 1 violations
4. **PR template** - Add reviewer checklist
5. **Monitor metrics** - Track adoption rates and PR velocity
6. **Quarterly review** - Adjust policy based on data

### Final Recommendation

**Yes, adopt this policy.** AAS is at a healthy baseline with clear improvement opportunities (ManagerHub, import patterns, test organization). A tiered "Leave It Better" policy with scope boundaries will accelerate adoption of new patterns without creating PR review bottlenecks.

**Start with Tier 1 mandatory + Tier 2 encouraged, then adjust based on data.**

---

**Document Version**: 1.0  
**Last Updated**: 2026-01-02  
**Owner**: AAS Core Team  
**Review Cycle**: Quarterly

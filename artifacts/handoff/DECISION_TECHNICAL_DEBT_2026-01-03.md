# Technical Debt Resolution - Decision Document
**Date:** January 3, 2026  
**Requestor:** GitHub Copilot  
**Reviewer:** Sixth  
**Context:** Post-AAS-114 codebase health assessment

---

## Executive Summary

After completing AAS-114 (gRPC Task Broadcasting) and file size optimization, a comprehensive scan revealed **critical import errors** and **type safety issues** that are blocking proper static analysis. Three resolution paths are proposed below.

---

## Current Issues Identified

### 🚨 **Critical (Blocking)**

| Issue | Location | Impact | Root Cause |
|-------|----------|--------|------------|
| Missing `core.handoff.manager` import | `core/managers/tasks.py:56`<br>`core/main.py:8` | Import errors prevent module loading | Incomplete refactoring - `HandoffManager` logic moved to `TaskManager` but imports not updated |
| Missing `core.managers.health` import | `core/managers/tasks.py:533` | Health aggregation broken | Module doesn't exist or wrong path |
| SQLAlchemy ORM comparison errors | `core/managers/tasks.py:227, 246, 305, 416-417` | Type checker fails, potential runtime bugs | Using column objects in boolean context instead of query methods |

### 🟡 **High Priority (Quality)**

| Issue | Location | Impact | Severity |
|-------|----------|--------|----------|
| Test files scattered | `scripts/test_*.py` (15 files)<br>`tests/` (1 file) | Hard to run full test suite | Organization |
| No unit tests for core managers | `core/managers/` | Can't verify refactoring safety | Coverage gap |
| Type hints in gRPC stubs | `core/ipc/server.py:42, 54, 59` | Pylance warnings (cosmetic) | Generated code |

### 🟢 **Medium Priority (Debt)**

| Issue | Count | Impact |
|-------|-------|--------|
| Missing docstrings | 15+ functions | Hard to understand API |
| Markdown lint errors | 496 issues | Documentation quality |
| `sys.path.insert` boilerplate | 30 scripts | Import fragility |

---

## Option A: Foundation Fix (Quick Stabilization)

**Goal:** Make the codebase stable and type-safe  
**Effort:** 2-3 hours  
**Impact:** High - unblocks development

### Tasks

1. **Resolve HandoffManager Import Crisis**
   - **Option A1:** Create `core/handoff/manager.py` with stub/facade to `TaskManager`
   - **Option A2:** Update all imports to use `TaskManager` directly
   - **Recommendation:** A2 (cleaner, matches actual architecture)
   
2. **Fix SQLAlchemy Type Errors** (5 locations)
   ```python
   # ❌ Current (broken)
   if task.status != TaskStatus.QUEUED:
   
   # ✅ Fixed
   if task.status != TaskStatus.QUEUED.value:  # Compare to enum value
   # OR
   task = session.get(Task, task_id)  # Load first, then compare
   ```

3. **Reorganize Test Suite**
   - Move `scripts/test_*.py` → `tests/`
   - Create `tests/conftest.py` with shared fixtures
   - Update `pytest.ini`

4. **Add TaskManager Unit Tests**
   - Test task claiming (FCFS logic)
   - Test task completion flow
   - Test IPC broadcasting integration

### Pros ✅
- **Unblocks type checking** - Can use mypy/pylance reliably
- **Prevents runtime errors** - SQLAlchemy bugs could cause crashes
- **Enables confident refactoring** - Tests provide safety net
- **Quick wins** - Visible progress in 2-3 hours

### Cons ❌
- **Doesn't add features** - Pure maintenance work
- **Interrupts momentum** - Delays roadmap progress
- **May uncover more issues** - Fixing imports could reveal other problems

### Risks
- **Low** - All changes are local and testable
- **Rollback:** Easy - changes are additive (tests) or localized (imports)

---

## Option B: Push Forward with Features (Momentum Focus)

**Goal:** Continue roadmap (AAS-213: WebSockets) while documenting debt  
**Effort:** 1-2 hours  
**Impact:** Medium - delivers value but accrues debt

### Tasks

1. **Start AAS-213 (Live Event Stream)**
   - Implement WebSocket server in FastAPI
   - Connect to existing gRPC broadcast system
   - Build real-time task update feed

2. **Create Tech Debt Registry**
   - Document all known issues in `TECH_DEBT.md`
   - Tag each with severity and estimated fix time
   - Schedule "Stabilization Sprint" for next week

3. **Add Import Guards**
   ```python
   try:
       from core.handoff.manager import HandoffManager
   except ImportError:
       # Fallback or warning
       HandoffManager = None
   ```

### Pros ✅
- **Delivers user value** - Real-time monitoring is high-priority
- **Maintains momentum** - Roadmap stays on track
- **Deferred maintenance** - Can batch fixes later
- **Feature-driven** - More engaging than cleanup

### Cons ❌
- **Compounds tech debt** - Building on shaky foundation
- **Harder debugging** - Import errors will cause confusing failures
- **Quality risk** - New code inherits existing problems
- **Cognitive load** - Must remember to avoid broken modules

### Risks
- **Medium** - Could hit runtime errors from import issues
- **Rollback:** Medium - new feature intertwines with broken code

---

## Option C: Infrastructure Hardening (Long-term Quality)

**Goal:** Build a robust, production-ready system  
**Effort:** 4-6 hours  
**Impact:** Very High - pays long-term dividends

### Tasks

1. **Implement Full Test Suite**
   - Add pytest with coverage tracking
   - Create mocks for Database, IPC, External APIs
   - Target 80%+ coverage for `core/managers/`

2. **Add Database Migrations (Alembic)**
   - Initialize Alembic (per AAS-032 completion report)
   - Generate initial migration from models
   - Add migration CI check

3. **Set Up CI/CD Pipeline**
   ```yaml
   # .github/workflows/ci.yml
   - Run pytest
   - Run mypy type checking
   - Check file sizes (<50MB)
   - Run markdown lint
   ```

4. **Create Health Check Endpoint**
   - Add `/health` API to FastAPI
   - Report status of: Database, IPC, TaskManager, Workspace
   - Enable monitoring/alerting

5. **Resolve All Import Errors** (same as Option A)

### Pros ✅
- **Professional grade** - System is production-ready
- **Prevents future debt** - CI catches issues early
- **Confidence in changes** - Comprehensive test coverage
- **Monitoring visibility** - Health checks aid debugging
- **Scalability** - Foundation supports growth

### Cons ❌
- **High time investment** - 4-6 hours upfront
- **Delayed features** - Roadmap pauses for quality
- **Learning curve** - Team needs to learn new tools (Alembic, CI)
- **Overkill risk** - May be over-engineering for current scale

### Risks
- **Low-Medium** - More moving parts, but well-tested
- **Rollback:** Hard - infrastructure changes are foundational

---

## Detailed Comparison Matrix

| Criteria | Option A: Foundation | Option B: Push Forward | Option C: Infrastructure | Weight |
|----------|---------------------|------------------------|--------------------------|--------|
| **Unblocks Development** | ✅ Yes | ⚠️ Partial | ✅ Yes | 🔥 High |
| **Delivers User Value** | ❌ No | ✅ Yes (AAS-213) | ❌ No | 🔥 High |
| **Prevents Future Bugs** | ⚠️ Some | ❌ No | ✅ Strongly | 🟡 Medium |
| **Time to Complete** | 2-3 hrs ✅ | 1-2 hrs ✅✅ | 4-6 hrs ⚠️ | 🔥 High |
| **Enables Confident Refactoring** | ⚠️ Partial | ❌ No | ✅ Yes | 🟡 Medium |
| **Improves Onboarding** | ⚠️ Some | ❌ No | ✅ Yes (tests+CI) | 🟢 Low |
| **Risk of Disruption** | 🟢 Low | 🟡 Medium | 🟡 Medium | 🟡 Medium |
| **Alignment with Roadmap** | ⚠️ Neutral | ✅ Aligned | ❌ Off-track | 🔥 High |
| **Technical Debt Reduction** | ⚠️ -30% | ❌ +10% | ✅ -80% | 🟡 Medium |

**Legend:** ✅ Strong | ⚠️ Partial | ❌ Weak  
**Weights:** 🔥 High | 🟡 Medium | 🟢 Low

---

## Hybrid Option: A + B Phased (Recommended)

**Phase 1 (Today, 1 hour):** Quick fixes to unblock
1. Fix HandoffManager imports (30 min)
2. Fix critical SQLAlchemy errors (30 min)

**Phase 2 (Tomorrow, 2 hours):** Start AAS-213
3. Implement WebSocket event stream
4. Connect to gRPC broadcasts

**Phase 3 (Next Week):** Infrastructure sprint
5. Full test suite + CI/CD
6. Database migrations

### Rationale
- **Balanced approach** - Fixes blockers without stalling features
- **Progressive enhancement** - Each phase adds value
- **Lower risk** - Small, testable increments
- **Flexibility** - Can re-prioritize after each phase

---

## Questions for Sixth

Please answer these to help finalize the decision:

### 1. **Urgency Assessment**
- **Q:** Are the import errors causing active runtime failures, or just type checker warnings?
- **Options:**
  - [ ] **Blocking production** → Must fix immediately (Option A)
  - [ ] **Annoying but functional** → Can defer (Option B)
  - [ ] **Unknown** → Need to test (run `python core/main.py`)

### 2. **Roadmap Priorities**
- **Q:** Is AAS-213 (WebSockets) a hard deadline or can we pause for quality?
- **Options:**
  - [ ] **Hard deadline** → Option B (features first)
  - [ ] **Flexible** → Option A or Hybrid
  - [ ] **Quality matters more** → Option C

### 3. **Team Capacity**
- **Q:** How much time can we allocate to maintenance vs. features this week?
- **Options:**
  - [ ] **< 2 hours** → Option B (minimal)
  - [ ] **2-4 hours** → Option A or Hybrid Phase 1-2
  - [ ] **> 4 hours** → Option C (full hardening)

### 4. **Risk Tolerance**
- **Q:** How comfortable are we building new features on the current foundation?
- **Options:**
  - [ ] **High risk tolerance** → Option B (ship fast, fix later)
  - [ ] **Moderate** → Hybrid (fix blockers, then build)
  - [ ] **Low** → Option A or C (stabilize first)

### 5. **Technical Preference**
- **Q:** Which aspect of quality is most important right now?
- **Rank these (1=most important, 5=least):**
  - [ ] ___ Type safety (mypy/pylance working)
  - [ ] ___ Test coverage (unit tests for managers)
  - [ ] ___ CI/CD automation (GitHub Actions)
  - [ ] ___ Database migrations (Alembic)
  - [ ] ___ Feature delivery (AAS-213 WebSockets)

---

## Copilot's Recommendation

**Hybrid Option (A + B Phased)** - Fix the import/type blockers NOW (1 hour), then proceed with AAS-213. Schedule infrastructure work for next week.

**Rationale:**
1. Import errors are ticking time bombs - they WILL cause runtime failures
2. AAS-213 builds naturally on AAS-114's gRPC work
3. Splitting work keeps momentum while addressing critical issues
4. Tests + CI can wait until after we have a few more features to test

**If forced to choose one:**
- **For stability:** Option A
- **For velocity:** Option B
- **For long-term:** Option C

---

## Next Steps (Pending Sixth's Input)

Once Sixth responds:
1. **Create task in ACTIVE_TASKS.md** with chosen option
2. **Estimate completion time** based on selected scope
3. **Assign to appropriate agent** (Copilot, Sixth, or coordinate)
4. **Set acceptance criteria** based on option's task list
5. **Execute and report back**

---

## Additional Context

### File Size Optimization (Completed ✅)
- Already addressed large file issues
- `.gitignore` updated to prevent future problems
- `FILE_SIZE_STRATEGY.md` created for reference

### Recent Completions
- ✅ AAS-113: Unified Task Manager
- ✅ AAS-114: gRPC Task Broadcasting
- ✅ File size strategy and git history cleanup

### Current System Status
- **Repo size:** 460 MB (clean)
- **Active tasks:** 15 queued
- **Test coverage:** Minimal (~5% estimated)
- **Type check status:** ❌ Failing (import errors)

---

**Sixth, please review the options above and answer the 5 questions. This will help us choose the right path forward.**

**Estimated Response Time:** 15-30 minutes for review + questions

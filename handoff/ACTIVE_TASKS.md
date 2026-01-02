# AAS Active Task Board

This is the local source of truth for task delegation. AI actors claim tasks by updating the `Status` and `Assignee` columns.

| ID | Priority | Title | Depends On | Status | Assignee | Created | Updated |
|:---|:---|:---|:---|:---|:---|:---|:---|
 | AAS-001 | Urgent | Redo delegation process to FCFS | - | Done | Sixth | 2026-01-02 | 2026-01-02 | 
 | AAS-002 | High | Test FCFS Claiming | AAS-001 | In Progress | CodeGPT | 2026-01-02 | 2026-01-02 | 
 | AAS-003 | Urgent | Implement Pydantic RCS | - | In Progress | Copilot | 2026-01-02 | 2026-01-02 | 
 | AAS-005 | Urgent | Add Task Dependencies to Handoff | AAS-001 | queued | - | 2026-01-02 | 2026-01-02 | 
 | AAS-006 | High | Enhance Health Monitoring | AAS-005 | queued | - | 2026-01-02 | 2026-01-02 | 
 | AAS-004 | High | Connect Linear API (Bi-directional Sync) | AAS-003 | queued | - | 2026-01-02 | 2026-01-02 | 
 | AAS-007 | High | Integrate LangGraph for Agentic Workflows | AAS-003 | queued | - | 2026-01-02 | 2026-01-02 | 
 | AAS-012 | Medium | AutoWizard101 Migration | - | queued | - | 2026-01-02 | 2026-01-02 | 
 | AAS-008 | Medium | Local LLM Support (Ollama) | AAS-003 | queued | - | 2026-01-02 | 2026-01-02 | 
 | AAS-009 | Medium | Home Assistant Integration | AAS-003 | queued | - | 2026-01-02 | 2026-01-02 | 
 | AAS-010 | Medium | Multi-Modal Vision Research | AAS-007 | queued | - | 2026-01-02 | 2026-01-02 | 
 | AAS-011 | Medium | Autonomous SysAdmin | AAS-006 | queued | - | 2026-01-02 | 2026-01-02 | 
 | AAS-013 | Low | Deimos-Wizard101 Port | AAS-012 | queued | - | 2026-01-02 | 2026-01-02 | 
 | AAS-014 | Low | DanceBot Integration | AAS-012 | queued | - | 2026-01-02 | 2026-01-02 | 

## Task Details

### AAS-001: Redo delegation process to FCFS
- **Description**: Transition from rigid role-based delegation to a first-come-first-serve "i-called-it" system using a local Markdown registry.
- **Acceptance Criteria**:
    - [x] Create `handoff/ACTIVE_TASKS.md`.
    - [x] Update delegation policy.
    - [x] Update handoff contract.
    - [x] Implement local claiming logic in `HandoffManager`.
    - [x] Add CLI shortcut for claiming.

### AAS-003: Implement Pydantic RCS
- **Description**: Replace the basic config manager with a Pydantic-based Resilient Configuration System.
- **Acceptance Criteria**:
    - [ ] Define Pydantic models for all config sections.
    - [ ] Implement environment variable override logic.
    - [ ] Add validation for critical keys (API keys, paths).
    - [ ] Migrate `core/config/manager.py` to use the new system.

### AAS-004: Connect Linear API (Bi-directional Sync)
- **Description**: Implement full sync between local `ACTIVE_TASKS.md` and Linear.
- **Acceptance Criteria**:
    - [ ] Pull new issues from Linear.
    - [ ] Push local status updates to Linear.
    - [ ] Sync comments/events.

### AAS-005: Add Task Dependencies to Handoff
- **Description**: Update `HandoffManager` to respect the `Depends On` column.
- **Acceptance Criteria**:
    - [x] Update `claim_next_task` to check dependency status.
    - [x] Skip tasks if dependencies are not 'Done'.
    - [ ] Update CLI to show blocked tasks.

### AAS-006: Enhance Health Monitoring
- **Description**: Improve `HealthAggregator` and `HandoffManager.generate_health_report` to include task board health.
- **Acceptance Criteria**:
    - [ ] Detect stale tasks (In Progress for > 3 days).
    - [ ] Detect unassigned high-priority tasks.
    - [ ] Check for missing artifact directories.

### AAS-007: Integrate LangGraph for Agentic Workflows
- **Description**: Use LangGraph to allow AAS to decompose complex tasks into sub-tasks automatically.
- **Acceptance Criteria**:
    - [ ] Define state graph for task decomposition.
    - [ ] Implement "Decomposer" node that writes to `ACTIVE_TASKS.md`.
    - [ ] Integrate with `HandoffManager`.

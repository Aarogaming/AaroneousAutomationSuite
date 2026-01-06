# Agent Collaboration System - Quick Start Guide

## Overview

The AAS Agent Collaboration System enables multiple AI agents (GitHub Copilot, ChatGPT, Claude, Sixth, Cline, etc.) to work together on tasks without stepping on each other's toes.

**Key Features:**
- ✅ Agent check-in/check-out with capability profiles
- ✅ Automatic capability matching for task assignment
- ✅ Help request protocol for collaboration
- ✅ Task locking to prevent conflicts
- ✅ Non-exclusive helper locks for code reviews

## Quick Start

### 1. Check In as an Agent

When starting work, check in to announce your presence and capabilities:

```bash
# CLI
python scripts/aas_cli.py agent checkin "GitHub Copilot" --version "1.0"

# Python
from core.managers import ManagerHub

hub = ManagerHub.create()
session_id = hub.collaboration.check_in("GitHub Copilot", agent_version="1.0")
print(f"Session ID: {session_id}")  # Save this!
```

**Supported Agents:** GitHub Copilot, ChatGPT, Claude, Sixth, Cline

Each agent has a pre-configured capability profile including:
- Strengths (e.g., refactoring, debugging, architecture)
- Supported languages
- Context window size
- Best use cases

### 2. View Active Roster

See who else is working:

```bash
# CLI
python scripts/aas_cli.py agent roster

# Python
active_agents = hub.collaboration.get_active_agents()
for agent in active_agents:
    print(f"{agent['agent_name']}: {agent['capabilities']['best_for']}")
```

### 3. Find Best Agent for a Task

Let the system recommend the best agent based on task requirements:

```bash
# CLI
python scripts/aas_cli.py agent find-agent \
  --task-desc "Refactor 500-line class with comprehensive tests" \
  --tags "refactoring,testing,documentation"

# Python
best_agent = hub.collaboration.find_best_agent_for_task(
    task_description="Refactor 500-line class with comprehensive tests",
    task_tags=["refactoring", "testing", "documentation"]
)

if best_agent:
    print(f"Best match: {best_agent['agent_name']} ({best_agent['match_score']*100:.0f}%)")
```

**Match Score Calculation:**
- Tag matches with "best_for" capabilities: +0.3 per tag
- Description keywords in strengths: +0.2 per match
- Large context window bonus for complex tasks: +0.1 to +0.4
- Workload penalty: -0.1 per active task

### 4. Request Help from Another Agent

When you need assistance without giving up task ownership:

```bash
# CLI
python scripts/aas_cli.py agent help-request AAS-123 <your-session-id> \
  --type code_review \
  --urgency high \
  --context "Need review on refactoring before commit. 200 lines changed." \
  --estimated-time 15

# Python
request_id = hub.collaboration.request_help(
    task_id="AAS-123",
    requester_session_id=your_session_id,
    help_type="code_review",  # or: debugging, architecture, testing, refactoring
    context="Need review on refactoring before commit. 200 lines changed.",
    urgency="high",  # low, medium, high, critical
    estimated_time=15  # minutes
)
```

**Help Types:**
- `code_review` - Review code changes
- `debugging` - Help troubleshoot issues
- `architecture` - Design decisions and system structure
- `testing` - Test strategy and implementation
- `refactoring` - Code restructuring advice

### 5. Accept a Help Request

When you see a help request you can assist with:

```bash
# List open requests
python scripts/aas_cli.py agent help-list

# Accept one
python scripts/aas_cli.py agent help-accept <request-id> <your-session-id> \
  --message "I'll review the refactoring now!"

# Python
success = hub.collaboration.accept_help_request(
    request_id="help-abc123",
    helper_session_id=your_session_id,
    response_message="I'll review the refactoring now!"
)
```

**What Happens:**
- Helper acquires a non-exclusive "helper" lock
- Multiple agents can help simultaneously
- Original task owner retains "active" lock
- Collaboration is tracked in database

### 6. Complete Help Request

After providing assistance:

```bash
# CLI
python scripts/aas_cli.py agent help-complete <request-id> \
  --outcome "Reviewed code. Suggested minor improvements to error handling. LGTM!"

# Python
hub.collaboration.complete_help_request(
    request_id="help-abc123",
    outcome="Reviewed code. Suggested minor improvements. LGTM!"
)
```

### 7. Check Out When Done

Always check out to release resources:

```bash
# CLI
python scripts/aas_cli.py agent checkout <your-session-id>

# Python
hub.collaboration.check_out(your_session_id)
```

## Task Locking

### Lock Types

1. **Active Lock** - Full task control
   - Only one agent can have active lock
   - Required to make changes
   - Auto-expires after 60 minutes (configurable)

2. **Soft Lock** - Intent to claim
   - Signals "I'm about to work on this"
   - Prevents others from claiming
   - Lighter weight than active lock

3. **Helper Lock** - Read-only assistance
   - Non-exclusive (multiple helpers allowed)
   - For code reviews and consultation
   - Auto-expires after 2 hours

### Acquiring Locks

```python
# Acquire active lock (exclusive)
success = hub.collaboration.acquire_task_lock(
    task_id="AAS-123",
    session_id=your_session_id,
    lock_type="active",
    timeout_minutes=60
)

# Acquire helper lock (non-exclusive, automatic via help requests)
# Just accept a help request - helper lock is created automatically

# Release lock
hub.collaboration.release_task_lock("AAS-123", your_session_id)
```

### Lock Conflict Prevention

- System checks for existing locks before granting
- Expired locks are automatically removed
- Lock heartbeat system prevents stale locks
- Clear error messages when lock is held by another agent

## Agent Capability Profiles

### GitHub Copilot
- **Strengths:** code_completion, refactoring, debugging, documentation
- **Best For:** incremental_changes, code_review, quick_fixes
- **Context:** Large
- **Languages:** Python, TypeScript, JavaScript, C#

### ChatGPT
- **Strengths:** planning, architecture, research, problem_solving
- **Best For:** system_design, complex_analysis, multi_step_tasks
- **Context:** XLarge
- **Languages:** Python, JavaScript, General

### Claude / Sixth
- **Strengths:** analysis, documentation, testing, code_generation
- **Best For:** large_refactors, comprehensive_docs, test_suites
- **Context:** XXLarge
- **Languages:** Python, JavaScript, Markdown

### Cline
- **Strengths:** autonomous_execution, file_operations, shell_commands
- **Best For:** automation, batch_operations, file_management
- **Context:** Medium
- **Languages:** Python, JavaScript, Bash

## Best Practices

### 1. Always Check In First
```python
# ✅ Good
session_id = hub.collaboration.check_in("ChatGPT")
# ... do work ...
hub.collaboration.check_out(session_id)

# ❌ Bad - working without checking in
# No visibility, no capability matching, no conflict prevention
```

### 2. Use the Right Help Type
```python
# ✅ Good - specific help types
hub.collaboration.request_help(..., help_type="code_review")
hub.collaboration.request_help(..., help_type="debugging")

# ❌ Bad - vague or wrong help type
hub.collaboration.request_help(..., help_type="general_help")
```

### 3. Set Realistic Urgency
```python
# ✅ Good - accurate urgency
urgency="low"      # Can wait a few hours
urgency="medium"   # Would like today
urgency="high"     # Need within the hour
urgency="critical" # Blocking other work

# ❌ Bad - everything is critical
urgency="critical"  # For every request
```

### 4. Provide Context
```python
# ✅ Good - specific context
context="Need review on refactoring TaskManager class. Changed 200 lines, extracted 3 new classes, added tests. Main concern is error handling in batch processor."

# ❌ Bad - vague context
context="Need help with code"
```

### 5. Clean Up After Yourself
```python
# ✅ Good - always check out
try:
    session_id = hub.collaboration.check_in("Copilot")
    # ... work ...
finally:
    hub.collaboration.check_out(session_id)

# ❌ Bad - leaving session active
session_id = hub.collaboration.check_in("Copilot")
# ... work ...
# Oops, forgot to check out!
```

## Run the Demo

See the full collaboration workflow in action:

```bash
python scripts/demo_agent_collaboration.py
```

**Demo Steps:**
1. Three agents check in (Copilot, ChatGPT, Sixth)
2. System displays active roster with capabilities
3. Find best agent for complex refactoring task
4. Agent conceptually acquires task lock
5. Agent requests help with code review
6. Another agent accepts help request
7. Help is completed with outcome summary
8. All agents check out cleanly

## Troubleshooting

### "Foreign Key Constraint Failed"
**Problem:** Trying to lock a task that doesn't exist in database  
**Solution:** Only lock tasks that exist in the Task table, or use None for conceptual demos

### "Task Already Locked"
**Problem:** Another agent has an active/soft lock  
**Solution:** Wait for lock to expire or request help instead (helper locks are non-exclusive)

### "Session Not Found"
**Problem:** Invalid or expired session_id  
**Solution:** Check in again to get a new session_id

### Duplicate Agents in Roster
**Problem:** Multiple check-ins without check-out  
**Solution:** Always check out when done, or query `WHERE status='active'` to see current state

## Integration with Existing Workflows

### Task Manager Integration

The collaboration system integrates seamlessly with AAS Task Manager:

```python
# Claim task with collaboration tracking
task = hub.tasks.claim_task("AAS-123")

# Check in as agent
session_id = hub.collaboration.check_in("GitHub Copilot")

# Acquire lock on claimed task
hub.collaboration.acquire_task_lock("AAS-123", session_id, lock_type="active")

# Work on task...

# Release lock and check out
hub.collaboration.release_task_lock("AAS-123", session_id)
hub.collaboration.check_out(session_id)

# Complete task
hub.tasks.complete_task("AAS-123")
```

### CLI Integration

All collaboration features available via unified CLI:

```bash
# Task workflow
aas task claim              # Claim next task
aas agent checkin "Copilot" # Check in
aas task status AAS-123     # Check task details
aas agent help-request ...  # Request help if needed
aas task complete AAS-123   # Complete task
aas agent checkout <id>     # Check out

# Batch workflow
aas batch submit AAS-123    # Submit to batch
aas agent roster            # See who's working
aas agent find-agent ...    # Find best agent for next task
```

## Database Schema

### agent_sessions
```sql
CREATE TABLE agent_sessions (
    id VARCHAR(50) PRIMARY KEY,           -- session-<uuid>
    agent_name VARCHAR(50),               -- "GitHub Copilot"
    agent_version VARCHAR(20),            -- "1.0"
    capabilities JSON,                    -- Capability profile
    status VARCHAR(20),                   -- active, idle, offline
    current_task_id VARCHAR(20),          -- FK to tasks
    checked_in_at DATETIME,
    last_activity DATETIME,
    heartbeat_interval INTEGER,           -- Seconds
    active_tasks_count INTEGER,
    completed_tasks_count INTEGER,
    help_requests_count INTEGER
)
```

### help_requests
```sql
CREATE TABLE help_requests (
    id VARCHAR(50) PRIMARY KEY,           -- help-<uuid>
    task_id VARCHAR(20),                  -- FK to tasks
    requester_session_id VARCHAR(50),     -- FK to agent_sessions
    helper_session_id VARCHAR(50),        -- FK to agent_sessions
    help_type VARCHAR(50),                -- code_review, debugging, etc.
    context TEXT,                         -- Description
    urgency VARCHAR(20),                  -- low, medium, high, critical
    estimated_time INTEGER,               -- Minutes
    status VARCHAR(20),                   -- open, accepted, completed, cancelled
    response_message TEXT,
    created_at DATETIME,
    accepted_at DATETIME,
    completed_at DATETIME
)
```

### task_locks
```sql
CREATE TABLE task_locks (
    task_id VARCHAR(20) PRIMARY KEY,      -- FK to tasks
    session_id VARCHAR(50),               -- FK to agent_sessions
    lock_type VARCHAR(20),                -- active, soft, helper
    acquired_at DATETIME,
    expires_at DATETIME,                  -- Auto-release
    last_heartbeat DATETIME
)
```

## Next Steps

- **Automated handoff:** System assigns tasks to best agent automatically
- **Workload balancing:** Distribute tasks based on agent capacity
- **Performance tracking:** Track agent efficiency and collaboration patterns
- **Team insights:** Dashboard showing collaboration metrics
- **Conflict resolution:** Auto-resolve lock conflicts with priority rules

---

**Need Help?** Check the main [AGENTS.md](../AGENTS.md) for broader AI collaboration protocols.

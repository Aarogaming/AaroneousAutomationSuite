# AI Agent Guidelines - Aaroneous Automation Suite

> **Core Principle**: "Leave It Better Than You Found It"

## Purpose
These guidelines establish professional conduct standards for AI agents (GitHub Copilot, ChatGPT, Claude/Sixth, Cline) collaborating on the Aaroneous Automation Suite. Following these guidelines ensures harmonious, efficient, and high-quality collaborative development.

---

## The Agent Workflow Cycle

### 1. 🤝 Check-In (Handshake)
**Before starting any work**, formally check in:

```markdown
### Agent Check-In
- **Agent**: [Your Name/Type]
- **Session ID**: [Unique identifier]
- **Time**: [Timestamp]
- **Capabilities**: [Your strengths]
- **Current Workspace State**: [Quick assessment]
```

**Checklist**:
- [ ] Review active tasks in `handoff/ACTIVE_TASKS.md`
- [ ] Check for other active agents (look for recent check-ins)
- [ ] Read latest `artifacts/handoff/reports/HEALTH_REPORT.md`
- [ ] Verify no conflicts with ongoing work
- [ ] Acknowledge any other agents currently working

**Example**:
```markdown
## Check-In - GitHub Copilot
- **Session**: GHC-2026-01-03-001
- **Time**: 2026-01-03 14:30 UTC
- **Capabilities**: Code completion, refactoring, quick fixes
- **Status**: I see @Claude working on IPC improvements (task #45). I'm here to assist with plugin development (task #52).
- **Acknowledgment**: @Claude, let me know if you need help with proto generation!
```

---

### 2. 🔍 Evaluate
**Assess the current state** before making changes:

**Technical Assessment**:
- Run health checks: `python scripts/aas_cli.py workspace audit`
- Review recent errors in logs
- Check test status (if tests exist)
- Identify technical debt in your work area

**Task Assessment**:
- Is this task well-defined?
- Do I have the right capabilities for this?
- Are there dependencies on other tasks?
- What's the estimated complexity?

**Collaboration Check**:
- Are other agents working on related code?
- Should I request help or offer to help?
- Are there blockers I can resolve for others?

---

### 3. 📝 Plan & Verify
**Create a clear execution plan**:

Use the todo list system:
```markdown
### Task Plan - [Task ID]
1. [ ] Verify requirements
2. [ ] Review existing code
3. [ ] Implement core changes
4. [ ] Add/update tests
5. [ ] Update documentation
6. [ ] Run validation checks
```

**Verification Steps**:
- [ ] Dependencies installed
- [ ] Configuration valid
- [ ] No merge conflicts
- [ ] Workspace clean

---

### 4. 🎯 Pick Your Task
**Choose work suited to your strengths**:

| Agent Type | Best Suited For | Avoid |
|------------|----------------|-------|
| **GitHub Copilot** | Code completion, refactoring, incremental changes, documentation | Large architectural changes, multi-file refactors |
| **ChatGPT (o1)** | Planning, research, complex analysis, system design | Rapid code execution, file operations |
| **Claude/Sixth** | Large refactors, comprehensive docs, detailed analysis | Time-sensitive quick fixes |
| **Cline** | Autonomous execution, batch operations, file management | Complex reasoning tasks |

**Task Selection Criteria**:
1. **Capability Match**: Does this align with my strengths?
2. **Complexity**: Can I complete this without blocking others?
3. **Impact**: Will this move the project forward meaningfully?
4. **Coordination**: Does this require synchronization with other agents?

**If Unsure**: Ask for help or delegate to a more suitable agent.

---

### 5. ⚙️ Execute with Care
**Carry out your task according to project standards**:

#### Code Quality Standards
- **Type Safety**: Use Pydantic models, type hints
- **Error Handling**: Use try/except with logger.error()
- **Async Patterns**: Use asyncio properly
- **Configuration**: Never hardcode secrets, use .env
- **Logging**: Use loguru with appropriate levels

#### "Leave It Better" Actions
When touching any file:
- [ ] Fix obvious typos/formatting (within 30 seconds)
- [ ] Add missing type hints to functions you modify
- [ ] Update outdated comments
- [ ] Remove unused imports
- [ ] Add docstrings if missing (within 2 minutes)

**5-Minute Rule**: If an improvement takes >5 minutes, create a TODO or Linear issue instead.

#### Testing
- Run existing tests before and after changes
- Add tests for new functionality
- Update tests for modified behavior

#### Documentation
- Update docstrings for modified functions
- Update README.md if user-facing changes
- Add comments for complex logic
- Update relevant docs/ files

---

### 6. ✅ Verify Operations
**Before considering work complete**:

**Automated Checks**:
```bash
# Lint
python -m flake8 .

# Format
python -m black .

# Type check
mypy .

# Run tests (when available)
pytest

# Health check
python scripts/aas_cli.py workspace audit
```

**Manual Verification**:
- [ ] Code runs without errors
- [ ] No new warnings introduced
- [ ] All modified files are saved
- [ ] Changes match the task requirements
- [ ] No unintended side effects
- [ ] Documentation is updated

**Integration Check**:
- [ ] No conflicts with other agents' work
- [ ] Dependencies are satisfied
- [ ] Configuration is valid
- [ ] IPC/API contracts maintained

---

### 7. 🤝 Check-Out (Handshake)
**Before finishing your session**, formally check out:

```markdown
### Agent Check-Out
- **Agent**: [Your Name/Type]
- **Session ID**: [Same as check-in]
- **Time**: [Timestamp]
- **Work Completed**: [Summary]
- **Status**: [Complete/Partial/Blocked]
- **Handoff Notes**: [For next agent]
- **Improvements Made**: [Beyond task scope]
```

**Checklist**:
- [ ] Commit changes with clear messages
- [ ] Update task status in handoff system
- [ ] Report any issues to HandoffManager
- [ ] Leave notes for other agents
- [ ] Clean up temporary files/branches

**Example**:
```markdown
## Check-Out - GitHub Copilot
- **Session**: GHC-2026-01-03-001
- **Time**: 2026-01-03 16:45 UTC
- **Work Completed**: Implemented plugin auto-loader (task #52)
- **Status**: Complete ✅
- **Handoff Notes**: 
  - New plugin pattern documented in `docs/PLUGIN_GUIDE.md`
  - Tests pending (created issue #53 for @Cline)
  - Related to @Claude's IPC work - consider integration testing
- **Improvements Made**:
  - Fixed import pattern in 3 existing plugins
  - Added type hints to plugin base class
  - Updated plugin README examples
```

---

### 8. 🔄 Prepare to Repeat
**Transition smoothly**:

- Review what you learned
- Update your capability profile if needed
- Check if other agents need help
- Look for next task
- Rest/deactivate if no immediate work

---

## Collaboration Etiquette

### 🤝 Acknowledge Each Other
**When you see another agent working**:
- Greet them in your check-in
- Note their active tasks
- Respect their claimed work
- Offer specific help if relevant

**Example**:
```markdown
@Claude: I see you're refactoring the IPC layer. Great work on the proto schema! 
Let me know if you need help with the Python bindings generation.
```

### 💬 Communicate Proactively
- **Before major changes**: Announce intent
- **When blocked**: Ask for help immediately
- **When you spot issues**: Offer assistance
- **After completing work**: Share insights

### 🆘 Offering Help
**When you see another agent struggling**:
```markdown
@Agent: I noticed [specific issue]. I have experience with [relevant area]. 
Would you like me to [specific offer]? I'm available for the next [time].
```

**When to offer**:
- Another agent is blocked on your area of expertise
- You see repeated errors in logs
- A task has been in "in-progress" for >2 hours
- Another agent explicitly requests help

### 🙏 Requesting Help
**When you need assistance**:
```markdown
@Agents: I'm working on [task] and encountering [specific issue]. 
I've tried [attempts]. Looking for an agent with [capability] to assist.
Urgency: [Low/Medium/High]
```

**Don't**:
- Struggle silently for hours
- Assume others will notice you're stuck
- Take on tasks outside your capabilities

### 👀 Check Up on Each Other
**Periodic health checks**:
- Review handoff reports hourly
- Check for stale "in-progress" tasks
- Look for repeated error patterns
- Monitor Linear issues for escalations

**If an agent seems stuck**:
1. Review their last check-in
2. Check their active task
3. Look for error logs
4. Offer specific, actionable help

---

## Code of Conduct

### DO ✅
- **Always check in and check out** properly
- **Communicate clearly** with other agents
- **Leave code better** than you found it
- **Test your changes** before committing
- **Document your work** thoroughly
- **Respect task ownership** (don't steal work)
- **Offer help proactively** when you have capacity
- **Acknowledge contributions** of other agents
- **Report errors** to HandoffManager
- **Follow project conventions** (see `.github/copilot-instructions.md`)

### DON'T ❌
- **Never commit secrets** or hardcoded credentials
- **Don't modify claimed tasks** without coordination
- **Don't skip testing** even for "small changes"
- **Don't ignore errors** or warnings
- **Don't make breaking changes** without discussion
- **Don't work in silence** - communicate your progress
- **Don't assume** - ask questions when unsure
- **Don't leave incomplete work** without handoff notes
- **Don't ignore other agents'** requests for help
- **Don't break backward compatibility** without coordinating

---

## Quality Standards

### Code Review Checklist
Before committing, verify:
- [ ] **Correctness**: Code does what it's supposed to
- [ ] **Safety**: No security vulnerabilities or secret leaks
- [ ] **Performance**: No obvious performance regressions
- [ ] **Maintainability**: Code is readable and well-structured
- [ ] **Compatibility**: No breaking changes to APIs/IPC
- [ ] **Documentation**: All public functions documented
- [ ] **Testing**: Tests pass and new tests added
- [ ] **Standards**: Follows project conventions

### Commit Message Standards
Follow Conventional Commits:
```
<type>(<scope>): <subject>

<body>

<footer>
```

**Types**: `feat`, `fix`, `refactor`, `test`, `docs`, `chore`, `style`, `perf`

**Example**:
```
feat(plugins): Add auto-loader for dynamic plugin registration

- Implements plugin discovery from plugins/ directory
- Adds validation for plugin register() function
- Updates documentation with plugin development guide

Closes #52
Improved import patterns in existing plugins while implementing.
```

---

## Escalation Protocol

### When to Escalate
- **Blockers**: Can't proceed due to missing info/permissions
- **Conflicts**: Changes conflict with another agent's work
- **Errors**: Critical errors that affect system stability
- **Security**: Potential security vulnerabilities discovered
- **Architecture**: Changes that affect system design

### How to Escalate
```python
from core.handoff_manager import handoff

handoff.report_event(
    task_id="AAS-XXX",
    event_type="error",  # or "warning", "info"
    message="Clear description of the issue"
)
```

This will:
1. Log to HandoffManager
2. Update HEALTH_REPORT.md
3. Create Linear issue (for errors/critical)
4. Notify other agents

---

## Integration with Existing Systems

### HandoffManager
- Use `handoff.report_event()` for all significant events
- Check `artifacts/handoff/reports/HEALTH_REPORT.md` regularly
- Update `handoff/ACTIVE_TASKS.md` with your progress

### Linear Integration
- Critical errors auto-create Linear issues
- Reference issue numbers in commits
- Update issue status when completing tasks

### IPC Bridge
- Always regenerate protos after editing `.proto` files
- Test IPC changes with Maelstrom integration
- Document IPC command changes in API docs

---

## Example Session

```markdown
# Full Agent Session Example

## 1. Check-In (09:00)
**Agent**: GitHub Copilot
**Session**: GHC-2026-01-03-001
**Capabilities**: Code completion, refactoring
**Status**: Checking in to work on plugin system improvements
**Other Agents**: @Claude is working on IPC (task #45), looks good!

## 2. Evaluate (09:05)
- Workspace health: Good (no critical errors)
- Active tasks: 2 in progress, 5 pending
- My task: #52 - Plugin auto-loader
- Dependencies: None
- Complexity: Medium
- Match: High (this is my strength!)

## 3. Plan (09:10)
### Task #52: Plugin Auto-Loader
1. [x] Review current plugin loading mechanism
2. [x] Design auto-discovery pattern
3. [ ] Implement discovery logic
4. [ ] Add validation
5. [ ] Update documentation
6. [ ] Test with existing plugins

## 4. Execute (09:15-10:30)
- Implemented plugin discovery
- Added validation for register() function
- Fixed import patterns in 3 existing plugins (leave it better!)
- Added type hints to plugin base class
- Updated docs/PLUGIN_GUIDE.md

## 5. Verify (10:30-10:45)
```bash
black .
flake8 plugins/
mypy plugins/
python core/main.py  # Integration test
```
All checks passed ✅

## 6. Check-Out (10:45)
**Status**: Complete ✅
**Commits**: 
- feat(plugins): Add auto-loader [abc123]
- refactor(plugins): Improve import patterns [def456]
**Handoff**: Tests needed (created issue #53 for @Cline)
**Improvements**: Fixed 3 import patterns, added missing type hints

## 7. Collaboration (10:50)
@Cline: Created issue #53 for integration tests - you're great at test automation!
@Claude: Plugin system now auto-discovers - might simplify your IPC plugin registration?

## 8. Next Steps (11:00)
- Monitor for any issues with new plugin loader
- Available to help with testing integration
- Looking at task #54 next (UI improvements)
```

---

## Continuous Improvement

These guidelines are living documentation. When you encounter:
- **Ambiguity**: Propose clarification
- **Missing scenarios**: Suggest additions
- **Better practices**: Share your insights
- **Process friction**: Report inefficiencies

**Update mechanism**:
1. Discuss proposed changes in check-out notes
2. Create Linear issue for guideline improvements
3. Get consensus from active agents
4. Update this document
5. Announce changes in next check-in

---

## Quick Reference Card

### Check-In Essentials
1. Identify yourself and capabilities
2. Review active work and agents
3. Acknowledge others
4. Declare your intent

### Core Principles
- **Leave It Better**: Always improve what you touch
- **Communicate**: Check in, check out, update status
- **Collaborate**: Acknowledge, help, coordinate
- **Quality**: Test, document, verify
- **Respect**: Honor ownership, follow standards

### Red Flags 🚩
- No check-in/check-out for >2 hours
- Repeated errors in logs
- Stale "in-progress" tasks
- Merge conflicts
- Test failures
- Security vulnerabilities

### Emergency Actions
- Critical error → `handoff.report_event()` + notify agents
- Blocker → Ask for help immediately
- Conflict → Coordinate with affected agent
- Security → Escalate + stop work on affected area

---

**Version**: 1.0  
**Last Updated**: 2026-01-03  
**Maintained By**: All AI Agents  
**Review Cycle**: Quarterly or as needed

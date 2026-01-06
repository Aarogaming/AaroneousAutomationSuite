# AI Agent Quick Start Guide

> **For full guidelines, see [AI_AGENT_GUIDELINES.md](AI_AGENT_GUIDELINES.md)**

## Quick Check-In Template

```markdown
## Check-In - [Your Agent Name]
- **Session**: [ID]
- **Time**: [Timestamp]
- **Task**: [What you're working on]
- **Acknowledging**: [Other active agents]
```

## Essential Rules

1. **🤝 Always Check-In/Check-Out**: Let others know you're here and when you leave
2. **💚 Leave It Better**: Improve what you touch (5-minute rule)
3. **👥 Acknowledge Others**: Say hi to active agents, offer help
4. **✅ Verify Before Commit**: Test, lint, format
5. **📢 Communicate**: Don't work in silence

## Agent Strengths

| Agent | Best For |
|-------|----------|
| **GitHub Copilot** | Code completion, refactoring, quick fixes, documentation |
| **ChatGPT (o1)** | Planning, research, complex analysis, architecture |
| **Claude/Sixth** | Large refactors, comprehensive docs, detailed analysis |
| **Cline** | Autonomous execution, batch operations, file management |

## The Workflow Cycle

1. **Check-In** → 2. **Evaluate** → 3. **Plan** → 4. **Pick Task** → 5. **Execute** → 6. **Verify** → 7. **Check-Out** → 8. **Repeat**

## Quick Commands

```bash
# Health check
python scripts/aas_cli.py workspace audit

# Lint & format
python -m black .
python -m flake8 .
mypy .

# Run tests
pytest
```

## When to Ask for Help

- Blocked for >30 minutes
- Repeated errors
- Outside your expertise
- Breaking changes needed

## Emergency

```python
from core.handoff_manager import handoff
handoff.report_event("TASK-ID", "error", "Description")
```

---

**For detailed guidelines**: [AI_AGENT_GUIDELINES.md](AI_AGENT_GUIDELINES.md)  
**Collaboration System**: [docs/AGENT_COLLABORATION.md](docs/AGENT_COLLABORATION.md)  
**Leave It Better Policy**: [docs/LEAVE_IT_BETTER_POLICY.md](docs/LEAVE_IT_BETTER_POLICY.md)


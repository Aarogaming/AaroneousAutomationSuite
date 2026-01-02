# Maelstrom Agent Guidance

This document provides specific instructions for AI agents (Aider, Claude Code, Cline) operating within the Project Maelstrom codebase.

## Task Claiming
1. Check `handoff/ACTIVE_TASKS.md` for `queued` tasks.
2. Update the task status to `In Progress` and set `Assignee` to your agent name (e.g., `Aider`).
3. Register your session via `HandoffManager.register_background_agent()`.

## Worktree Isolation
Always create a dedicated worktree for your task:
```bash
git worktree add ../worktrees/AAS-XXX task-branch-name
```

## Code Style & Standards
- **Language**: C# 12 / .NET 8
- **UI**: WinForms (Legacy) / WPF (New)
- **Patterns**: MVVM for new components, Service-based architecture for logic.
- **Documentation**: Use XML comments for public methods.

## Testing
- Run tests before committing: `dotnet test ProjectMaelstrom.Tests`
- Ensure no regressions in OCR or Memory-level state logic.

## Handoff
Upon completion:
1. Push your branch.
2. Update `ACTIVE_TASKS.md` to `Done`.
3. Generate a `COMPLETION_REPORT.md` in `artifacts/handoff/AAS-XXX/`.

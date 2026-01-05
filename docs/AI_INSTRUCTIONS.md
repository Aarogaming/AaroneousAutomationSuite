# AI Instructions & Context

This document provides essential context for AI agents (like Sixth, ChatGPT, or Claude) working within the Aaroneous Automation Suite (AAS).

## Workspace Philosophy
- **Efficiency First:** Minimize token usage by focusing on relevant files.
- **Hygiene:** Keep the workspace clean. Use `WorkspaceCoordinator` for cleanup.
- **Automation:** Prefer automated solutions over manual steps.
- **Handoffs:** Use the `handoff/` directory and `Autonomous Handoff Protocol (AHP)` for task continuity.

## Key Directories
- `core/`: The heart of AAS. Contains managers, agents, and configuration.
- `plugins/`: Extensible features (AI Assistant, Game Bots, etc.).
- `artifacts/`: Centralized storage for builds, reports, and diagnostics.
- `docs/`: Project documentation (now includes consolidated maelstrom docs).
- `handoff/`: Active task tracking and handoff state.

## AI Evaluation & Readiness
- **Type Hinting:** All new Python code should use type hints.
- **Docstrings:** Use Google-style docstrings for all public methods and classes.
- **Testing:** New features must include tests in the `tests/` or `scripts/` directory.
- **Context Packs:** Before starting a complex task, check `artifacts/diagnostics/` for recent workspace health reports.

## Tool Usage Guidelines
- **`replace_in_file`**: Preferred for targeted edits.
- **`write_to_file`**: Use for new files or complete overhauls.
- **`execute_command`**: Use for running tests, cleanup scripts, or system operations.
- **`WorkspaceCoordinator`**: Run `defrag_workspace()` periodically to maintain order.

## Evaluation Benchmarks
AI performance is evaluated based on:
1. **Task Completion Rate:** Successful resolution of Linear/Handoff tasks.
2. **Code Quality:** Adherence to PEP 8 and project standards.
3. **Context Efficiency:** Ability to solve problems with minimal file reads.
4. **Self-Healing:** Ability to detect and fix workspace issues autonomously.

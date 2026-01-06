# AAS Project Index

This index provides a quick reference for the streamlined AAS architecture.

## Core Application (`core/`)
- **`core/managers/`**: Unified core managers.
    - `tasks.py`: Task orchestration (FCFS 2.0).
    - `workspace.py`: Hygiene and defragmentation.
    - `artifacts.py`: Shared storage abstraction.
    - `batch.py`: OpenAI Batch API operations.
    - `protocol.py`: Standard `ManagerProtocol`.
    - `adapters/`: API adapters (Linear, etc.).
- **`core/agents/`**: Agentic logic and workflows.
- **`core/config/`**: Configuration management (RCS).
- **`core/database/`**: Data persistence (SQLAlchemy).
- **`core/ipc/`**: gRPC bridge to Project Maelstrom.
- **`core/plugins/`**: Plugin base classes.

## Plugin Ecosystem (`plugins/`)
- **`ai_assistant/`**: AI research and assistance.
- **`deimos/`**: Wizard101 utility suite.
- **`dance_bot/`**: Wizard101 DanceBot integration.
- **`dev_studio/`**: Visual scripting and audits.
- **`home_assistant/`**: Home automation bridge.
- **`home_server/`**: Local service monitoring.
- **`imitation_learning/`**: RL agent logic.
- **`ngrok_plugin/`**: Tunnel management.
- **`sysadmin/`**: System utilities.
- **`gitkraken/`**: GitKraken integration.

## Supporting Files
- **`artifacts/`**: Build outputs, reports, and task data.
- **`docs/`**: Comprehensive documentation.
    - `MASTER_ROADMAP.md`: **Consolidated roadmap (2026-2027+)** - Start here!
    - `ROADMAP.md`: High-level 5-phase summary
    - `GAME_AUTOMATION_ROADMAP.md`: ML/RL learning pipeline (Phase 1-6, detailed)
    - `DESKTOP_GUI_ROADMAP.md`: Native desktop app implementation (5-week plan)
    - `AUTOMATION_ROADMAP.md`: Batch processing & task automation pipeline
    - `ROADMAP_INTEGRATION.md`: **NEW** - Automated task generation from roadmaps
    - `GAME_LEARNING_INTEGRATION.md`: Developer integration guide for ML components
    - `GAME_LEARNING_STATUS.md`: Current status & quick reference for game learning
    - `SECURITY_GUIDELINES.md`: **NEW** - Security best practices & credential management
    - `AI_AGENT_GUIDELINES.md`: Agent collaboration protocols
    - `AGENTS.md`: Quick reference for AI assistants
- **`scripts/`**: Utility scripts and unified CLI.
    - `pre-commit-security-check.ps1`: **NEW** - Pre-commit security scanner
- **`handoff/`**: Active task tracking (Markdown view).

## Key Entry Points
- **CLI**: `python scripts/aas_cli.py`
- **Hub**: `core/managers/__init__.py`
- **Config**: `core/config/manager.py`

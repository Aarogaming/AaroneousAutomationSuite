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
- **`scripts/`**: Utility scripts and unified CLI.
- **`handoff/`**: Active task tracking (Markdown view).

## Key Entry Points
- **CLI**: `python scripts/aas_cli.py`
- **Hub**: `core/managers/__init__.py`
- **Config**: `core/config/manager.py`

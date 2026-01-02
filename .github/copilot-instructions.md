# Aaroneous Automation Suite (AAS) - AI Agent Guidelines

## Project Overview
AAS is a Python-based orchestration hub for multi-purpose automation: game management (Wizard101), home automation, and AI-assisted research. It communicates with **Project Maelstrom** (C# game client) via gRPC and integrates with Linear for autonomous task management.

**Key Architecture Pattern:** The "Autonomous Handoff Protocol (AHP)" - a feedback loop between AAS Hub, Linear, and AI agents (ChatGPT, Sixth) to delegate, execute, and report on tasks.

## Core Components

### 1. Resilient Configuration System (RCS)
- **File:** `core/config/manager.py`
- Uses **Pydantic** with `SecretStr` for type-safe validation and local secret management
- **Always** load secrets from `.env`, never hardcode API keys
- Config validation failures should trigger graceful fallback, not crashes

```python
# Example: Adding a new config field
class AASConfig(BaseSettings):
    new_feature_enabled: bool = Field(default=False, alias="NEW_FEATURE_ENABLED")
```

### 2. Handoff Manager (AHP)
- **File:** `core/handoff/manager.py`
- Generates `HEALTH_REPORT.md` with errors, warnings, and TODOs
- Integrates with Linear API to auto-create issues for critical events
- **Pattern:** Use `report_event()` for any error that should propagate to Linear

### 3. IPC Bridge (gRPC)
- **Files:** `core/ipc/server.py`, `scripts/generate_protos.py`
- Handles communication with Project Maelstrom (C#)
- **Before editing IPC code:** Regenerate protos with `python scripts/generate_protos.py`
- Commands flow: Maelstrom → AAS Hub → Plugin ecosystem

### 4. Plugin System
- **Directory:** `plugins/`
- Each plugin is a self-contained module (e.g., `ai_assistant`, `home_server`, `imitation_learning`)
- **Pattern:** Plugins should expose a `register()` function and subscribe to Hub events
- No direct inter-plugin communication; route through Hub's event bus

## Developer Workflows

### Setup & Run
```bash
# Install dependencies
pip install -r requirements.txt

# Configure environment
cp .env.example .env  # Add your OPENAI_API_KEY, LINEAR_API_KEY

# Start the Hub
python core/main.py
```

### Code Quality
```bash
# Lint
python -m flake8 .

# Format
python -m black .

# Type checking
mypy .

# Run tests (when implemented)
python -m pytest
```

### gRPC Proto Generation
```bash
# After editing core/ipc/protos/bridge.proto
python scripts/generate_protos.py
```

### Handoff Protocol
1. Check `artifacts/handoff/reports/HEALTH_REPORT.md` for current system state
2. Review `handoff/registry.json` for active tasks
3. Use `handoff.report_event(task_id, "error", "message")` to escalate issues

## Project-Specific Conventions

### Branching & Commits
- Branch naming: `maelstrom/<short-task-name>`
- Commit style: Conventional commits (`feat:`, `fix:`, `refactor:`, `test:`, `docs:`)

### Error Handling Pattern
```python
from loguru import logger

try:
    # Operation
    result = risky_operation()
except SpecificError as e:
    logger.error(f"Operation failed: {e}")
    handoff.report_event(task_id, "error", str(e))
    # Attempt graceful recovery
```

### Logging Standards
- Use `loguru` exclusively (already configured in imports)
- Levels: `logger.debug()` for verbose, `logger.info()` for state changes, `logger.error()` for failures, `logger.critical()` for Hub shutdown events
- **Never log secrets:** Use `.get_secret_value()` carefully and don't log result

### Async Patterns
- All IPC operations are `async`/`await`
- Use `asyncio.create_task()` for concurrent operations
- Example: `ipc_task = asyncio.create_task(serve_ipc(port=config.ipc_port))`

## Integration Points

### Linear Sync
- **File:** `core/handoff/linear.py`
- Requires `LINEAR_API_KEY` and `LINEAR_TEAM_ID` in `.env`
- Auto-creates issues for `error` or `critical` events via `HandoffManager.report_event()`

### Project Maelstrom (C#)
- AAS is the "brain," Maelstrom is the "hands" controlling Wizard101
- Commands sent via gRPC: `ExecuteCommand`, `StreamSnapshots`
- **Security note:** IPC bridge currently uses insecure port; future work will add mTLS

### Plugin Integration
- Plugins are loaded from `plugins/` directory
- Expected structure: `plugins/<name>/__init__.py` with `register(hub: Hub)` function
- Plugins can request config via `hub.config.<field>`

## Critical DO NOTs
1. **Never commit secrets** - use `.env` and `.gitignore` them
2. **Don't modify proto files** without regenerating Python bindings
3. **No direct plugin-to-plugin calls** - use Hub's event system
4. **Don't break backward compatibility** with Maelstrom IPC without coordinating

## Future Evolution (see EVOLUTION_PLAN.md)
- Agentic workflows (LangGraph/CrewAI) in `ai_assistant` plugin
- Reinforcement learning loop in `imitation_learning`
- Voice-to-automation via Home Assistant integration
- Node-based visual scripting in `dev_studio`

## Key Files to Review
- [README.md](README.md) - Project mission and features
- [ROADMAP.md](ROADMAP.md) - Current development phase
- [EVOLUTION_PLAN.md](EVOLUTION_PLAN.md) - Long-term vision
- [AGENTS.md](AGENTS.md) - AI collaboration protocols (used by ChatGPT/Copilot)

## Testing Strategy
- **Current:** Manual testing via `python core/main.py`
- **Planned:** Pytest suite with fixtures for config, IPC mocking
- **When adding features:** Write tests first (TDD), add to `tests/` directory

## Quick Reference: Common Tasks

### Add a new config field
Edit `core/config/manager.py` → Add field to `AASConfig` → Update `.env.example`

### Create a new plugin
1. Create `plugins/<name>/__init__.py`
2. Implement `register(hub)` function
3. Subscribe to Hub events or expose new IPC commands

### Debug IPC issues
1. Check proto generation: `python scripts/generate_protos.py`
2. Verify Maelstrom connection in logs: `"Received command from Maelstrom"`
3. Inspect `_latest_snapshot` in `BridgeService`

### Report a task to Linear
```python
handoff.report_event(
    task_id="AAS-123",
    event_type="error",
    message="Plugin X failed to load: ModuleNotFoundError"
)
```

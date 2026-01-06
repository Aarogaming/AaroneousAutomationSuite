# AAS Workspace Structure

**Last Updated:** January 2, 2026  
**Status:** Defragmented & Optimized ✅

## Directory Organization

### Core Application
```
├── core/                   # AAS Hub core components
│   ├── config/            # Configuration management (RCS)
│   ├── handoff/           # Task & workspace management
│   ├── ipc/               # gRPC bridge to Project Maelstrom
│   ├── batch/             # Batch API integration
│   └── database/          # Data persistence
│
├── plugins/               # Plugin ecosystem
│   ├── ai_assistant/      # GPT-4/Claude integration
│   ├── dev_studio/        # Visual scripting (planned)
│   ├── home_assistant/    # Home automation bridge
│   ├── home_server/       # Local services
│   ├── imitation_learning/# RL agent (planned)
│   ├── ngrok_plugin/      # Tunnel management
│   └── sysadmin/          # System utilities
│
└── scripts/               # Utility scripts & CLI tools
    ├── task_manager_cli.py       # Unified task/workspace CLI
    ├── defrag_workspace.ps1      # Workspace cleanup
    ├── generate_protos.py        # gRPC proto generation
    └── sync_linear.py            # Linear integration
```

### Game Management
```
├── game_manager/          # Game automation orchestration
│   └── maelstrom/         # Project Maelstrom (C# game client)
│       ├── AutoWizard101/ # Legacy bot (being migrated)
│       ├── ProjectMaelstrom/ # Main C# application
│       ├── MaelstromBot.Server/ # gRPC server
│       ├── Plugins/       # C# plugin system
│       └── DevTools/      # Development utilities
│
└── Wizard101_DanceBot/    # Standalone Python bot
    ├── wizard101_dancebot/# Package source
    ├── assets/            # UI textures
    └── TCLChanger/        # Resolution adapter
```

### Supporting Files
```
├── artifacts/             # Build outputs & generated files
│   ├── builds/            # Compiled binaries & publish outputs
│   │   └── maelstrom_publish/ # Latest Maelstrom build
│   ├── handoff/           # Task management data
│   │   └── maelstrom/     # Project Maelstrom handoff logs
│   ├── ui_audits/         # UI screenshots & baseline tests
│   │   ├── ui_baseline/   # Reference UI screenshots
│   │   ├── ui_current/    # Current UI state
│   │   └── ui_audit_pack_selfcapture/ # Self-captured audits
│   └── batch/             # OpenAI Batch API jobs
│
├── docs/                  # Documentation
│   ├── maelstrom/         # Project Maelstrom docs
│   ├── ADAPTERS.md        # API adapter patterns
│   ├── AGENT_TOOLING.md   # AI agent workflows
│   └── WORKSPACE_COORDINATION.md # This file's companion
│
└── handoff/               # Active task tracking
    ├── ACTIVE_TASKS.md    # Current work items
    ├── COMPLETED_TASKS.md # Task history
    └── IMPROVEMENTS.md    # Enhancement backlog
```

## Key Principles

### 1. Separation of Concerns
- **Core**: Python orchestration hub
- **game_manager/maelstrom**: C# game automation
- **plugins**: Modular feature extensions
- **artifacts**: Ephemeral build outputs
- **docs**: Human-readable documentation

### 2. Build Output Isolation
- All compiled binaries → `artifacts/builds/`
- UI test screenshots → `artifacts/ui_audits/`
- Task reports → `artifacts/handoff/`
- Batch jobs → `artifacts/batch/`

### 3. Plugin Independence
- Each plugin is self-contained
- No direct inter-plugin dependencies
- Communication through Hub's event bus

### 4. Documentation Co-location
- Project-specific docs live near code
- Consolidated docs in `docs/` for cross-cutting concerns
- Handoff docs in `handoff/` for active task context

## Workspace Hygiene

### Automated Cleanup
The WorkspaceCoordinator (`core/handoff/workspace_coordinator.py`) maintains workspace health:

```bash
# Scan for issues
python scripts/task_manager_cli.py workspace-scan

# Find duplicates
python scripts/task_manager_cli.py workspace-duplicates

# Clean up (dry-run first!)
python scripts/task_manager_cli.py workspace-cleanup --dry-run
python scripts/task_manager_cli.py workspace-cleanup

# Health report
python scripts/task_manager_cli.py workspace-report
```

### Manual Defragmentation
```powershell
# Full restructure (as needed)
.\scripts\defrag_workspace.ps1
```

### Ignored Patterns
The following are automatically excluded from cleanup:
- `.git`, `.venv`, `.pytest_cache`
- `__pycache__`, `node_modules`
- `build`, `dist`, `*.egg-info`
- `bin`, `obj` (C# build artifacts)

## Recent Optimizations (Jan 2, 2026)

✅ **Duplicate Removal**: 15,982 files deleted (900 MB freed)
- WizWikiAPI scraped content (21+ copies → 1)
- Ingra project files (4 copies → 1)
- Wizard101_DanceBot (4 copies → 1)
- UI audit screenshots (3 copies → 1)

✅ **Directory Consolidation**:
- Fixed: `artifactshandoffmaelstrom/` → `artifacts/handoff/maelstrom/`
- Moved: `game_manager/maelstrom/publish/` → `artifacts/builds/`
- Moved: UI audit dirs → `artifacts/ui_audits/`
- Removed: Empty `New folder/`, duplicate `AutoWizard101/`

✅ **Health Score**: Excellent (0 duplicates, 0 temp files)

## Git Repository Management

This workspace tracks **3 repositories**:
1. **AaroneousAutomationSuite** (Aarogaming/AaroneousAutomationSuite)
   - Branch: `master`
   - Primary development hub

2. **Wizard101_DanceBot** (kennyhngo/Wizard101_DanceBot)
   - Branch: `main`
   - Active PR #10: MANIFEST.in

3. **AutoWizard101** (CoderJoeW/AutoWizard101)
   - Branch: `main`
   - Legacy bot being migrated to Maelstrom

**Note**: Each has independent `.git` directories. Use `git -C <path> <command>` for subproject operations.

## Evolution Plan

### Short-Term (Q1 2026)
- [ ] Complete Maelstrom IPC stabilization
- [ ] Migrate AutoWizard101 features to ProjectMaelstrom
- [ ] Implement voice-to-automation (Home Assistant bridge)

### Mid-Term (Q2-Q3 2026)
- [ ] Agentic workflows (LangGraph/CrewAI integration)
- [ ] Reinforcement learning for combat optimization
- [ ] Visual scripting in `dev_studio` plugin

### Long-Term (Q4 2026+)
- [ ] Multi-game support (expand beyond Wizard101)
- [ ] Community plugin marketplace
- [ ] Distributed execution across multiple machines

---

For detailed workspace coordination features, see [WORKSPACE_COORDINATION.md](WORKSPACE_COORDINATION.md).

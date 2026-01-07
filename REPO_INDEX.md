# Aaroneous Automation Suite (AAS) - Repository Index

This document provides a comprehensive overview of the Aaroneous Automation Suite repository structure, key components, and documentation.

## 📂 Project Structure

### 🏗️ Core Framework (`core/`)
The heart of AAS, containing the main logic and management systems.
- **`core/managers/`**: Unified core managers for tasks, workspace, artifacts, and more.
- **`core/agents/`**: Agentic logic and workflow implementations.
- **`core/config/`**: Configuration management system.
- **`core/database/`**: Data persistence layer using SQLAlchemy.
- **`core/ipc/`**: Inter-process communication (gRPC bridge).
- **`core/plugins/`**: Base classes and registry for the plugin system.

### 🧩 Plugin Ecosystem (`plugins/`)
Extensible modules that add specific functionality to AAS.
- **`ai_assistant/`**: AI research and assistance tools.
- **`deimos/`**: Wizard101 utility suite.
- **`dev_studio/`**: Visual scripting and UI audits.
- **`sysadmin/`**: System utilities and automation.
- **`gitkraken/`**: Integration with GitKraken workflows.

### 🖥️ User Interfaces
- **`dashboard/`**: Vite-based web dashboard for monitoring and control.
- **`HandoffTray/`**: System tray application for quick access.
- **`ProjectMaelstrom/`**: Core UI and automation components.

### ⚙️ C# Automation & Utilities
A collection of .NET-based tools for low-level automation and system integration.
- **`ProjectMaelstrom/`**: Main C# automation engine.
- **`MaelstromBot.Server/`**: Server component for Maelstrom.
- **`HandoffBridge/`, `HandoffTray/`, `HandoffUtility/`**: Components of the Autonomous Handoff Protocol.
- **`UiAuditRunner/`, `UiAuditDiff/`, `UiAuditSelfCapture/`**: UI auditing and testing tools.
- **`FunctionalTestRunner/`**: Automated functional testing suite.
- **`Utilities/`**: Shared C# utility libraries.

### 🛠️ Tooling & Scripts (`scripts/`, `tools/`)
- **`scripts/aas_cli.py`**: The primary command-line interface for AAS.
- **`scripts/pre-commit-security-check.ps1`**: Security scanner for commits.
- **`tools/`**: Miscellaneous helper tools and utilities.

### 🧪 Testing & Evaluation (`tests/`, `evals/`)
- **`tests/`**: Unit and integration tests.
- **`evals/`**: Evaluation templates and results for AI components.
- **`FunctionalTestRunner/`**: C#-based functional testing suite.

### 📚 Documentation (`docs/`)
Comprehensive guides and roadmaps.
- **`docs/MASTER_ROADMAP.md`**: The consolidated long-term roadmap.
- **`docs/INDEX.md`**: Quick reference for the streamlined architecture.
- **`docs/MANAGER_INDEX.md`**: Index of manager-specific improvements and docs.
- **`docs/AI_AGENT_GUIDELINES.md`**: Protocols for agent collaboration.

## 🚀 Key Entry Points
- **Main CLI**: `python scripts/aas_cli.py`
- **Web Dashboard**: Located in `dashboard/` (run via `npm run dev`)
- **Core Hub**: `core/managers/__init__.py`

## 📊 Data & Artifacts
- **`artifacts/`**: Build outputs, logs, reports, and shared data.
- **`handoff/`**: Active task tracking and handoff data.

---
*Last Updated: January 6, 2026*

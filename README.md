# Aaroneous Automation Suite (AAS) - Integration Hub

AAS serves as the **central integration hub** for the Aaroneous Dev Library, enabling cross-project communication via **schema-validated IPC** (Inter-Process Communication). It provides a reliable, versioned contract system for components to exchange data without tight coupling.

## Unified Ecosystem Architecture
- **AAS Hub (Python):** The central orchestrator for plugins, AI assistance, and home server management.
- **Project Maelstrom (C#):** Located in `game_manager/maelstrom`, handling memory-level state and UI automation.
- **Deimos (Python):** Located in `core/deimos`, providing advanced logic and questing capabilities.
- **DanceBot (Python):** Located in `plugins/dance_bot`, specialized automation for game mini-games.
- **IPC Backbone (C#):** File-based messaging system for cross-project data exchange.

For a detailed project index, see [docs/INDEX.md](docs/INDEX.md).

## Key Features
- **Resilient Configuration:** Type-safe validation with Pydantic and secure local secret management.
- **Autonomous Handoff Protocol (AHP):** A seamless development loop between Linear, ChatGPT 5.2 Pro, and Sixth.
- **Onboard AI Assistant:** Integrated GPT-5.2 Pro for real-time strategy and code generation.
- **Watch and Learn:** Imitation learning plugin to record and automate player actions in any game (see [Game Automation Roadmap](docs/GAME_AUTOMATION_ROADMAP.md)).
- **AAS Dev Studio:** Internal code editor and terminal for self-building capabilities.
- **IPC System:** Schema-validated messaging for reliable inter-component communication.

## IPC Quick Start

### Launch Router
```powershell
.\eng/ipc-router.ps1  # Continuous routing
```

### Add Consumer
```powershell
.\eng/ipc-consumer-loop.ps1 -Channel commands -ConsumerId myWorker
```

### Validate Contracts
```powershell
.\eng\validate-contracts.ps1
```

See [docs/ipc/IPC_CONVENTIONS.md](docs/ipc/IPC_CONVENTIONS.md) for full IPC guide.

## Getting Started
1. Install Python 3.12 and create a venv: `py -3.12 -m venv .venv`
2. Activate the venv: `.\.venv\Scripts\activate` (Windows) or `source .venv/bin/activate` (macOS/Linux)
3. Install dependencies: `python -m pip install -r requirements.txt`
4. Configure your local environment in `.env` (OpenAI API Key, etc.)
5. Start the Hub: `python hub.py`
6. Recommended: one-step launch with prep & readiness checks: `python scripts/aas_launcher.py launch --wait`

## Project Maelstrom (Game Automation)
The Wizard101/Maelstrom game automation stack has been split into its own repo: https://github.com/Aarogaming/AutoWizard101.git. Use that project for game-side bots, server, and toolkit; AAS will integrate via plugins/APIs when needed.

## Game Learning Initiative 🎮🧠

AAS is evolving toward **autonomous game learning** through behavioral cloning and reinforcement learning.

**Current Status**: Foundation built, training pipeline in development  
**Goal**: AI agent that "watches" gameplay and learns to replicate complex behaviors  
**Timeline**: 9-12 months to working policy

### Quick Links
- 📋 [Full Roadmap](docs/GAME_AUTOMATION_ROADMAP.md) - 6-phase plan with technical details
- 🛠️ [Integration Guide](docs/GAME_LEARNING_INTEGRATION.md) - For developers implementing features
- 📊 [Status Tracker](docs/GAME_LEARNING_STATUS.md) - Current progress and next steps

### What Works Today
- ✅ Record gameplay sessions (state + actions)
- ✅ Vision-based UI analysis (GPT-4o)
- ✅ Real-time game state streaming (gRPC)
- ✅ Pre-built automation bots

# Aaroneous Automation Suite (AAS)

## Overview
Aaroneous Automation Suite is an open-source, multi-purpose automation ecosystem. It is designed to act as a central hub for high-performance game management, home automation, and AI-assisted research.

## Unified Ecosystem Architecture
- **AAS Hub (Python):** The central orchestrator for plugins, AI assistance, and home server management.
- **Project Maelstrom (C#):** Located in `game_manager/maelstrom`, handling memory-level state and UI automation.
- **Deimos (Python):** Located in `core/deimos`, providing advanced logic and questing capabilities.
- **DanceBot (Python):** Located in `plugins/dance_bot`, specialized automation for game mini-games.

For a detailed project index, see [docs/INDEX.md](docs/INDEX.md).

## Key Features
- **Resilient Configuration:** Type-safe validation with Pydantic and secure local secret management.
- **Autonomous Handoff Protocol (AHP):** A seamless development loop between Linear, ChatGPT 5.2 Pro, and Sixth.
- **Onboard AI Assistant:** Integrated GPT-5.2 Pro for real-time strategy and code generation.
- **Watch and Learn:** Imitation learning plugin to record and automate player actions in any game (see [Game Automation Roadmap](docs/GAME_AUTOMATION_ROADMAP.md)).
- **AAS Dev Studio:** Internal code editor and terminal for self-building capabilities.

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

### What's Coming
- 🔄 Phase 1 (Months 1-2): Enhanced data collection
- 🔄 Phase 2 (Months 2-4): Vision encoder training
- 🚀 Phase 3 (Months 4-7): First trained policy
- 🎯 Phase 4 (Months 7-9): Ghost mode (human-in-the-loop)

Want to contribute? See [GAME_LEARNING_STATUS.md](docs/GAME_LEARNING_STATUS.md) for ways to help.

## 📚 Documentation

### Roadmaps
- 🗺️ **[Master Roadmap](docs/MASTER_ROADMAP.md)** - Unified timeline and strategy (2026-2027+)
- 📋 [Phase Overview](docs/ROADMAP.md) - High-level 5-phase summary
- 🎮 [Game Automation](docs/GAME_AUTOMATION_ROADMAP.md) - 6-phase ML/RL learning system
- 🖥️ [Desktop GUI](docs/DESKTOP_GUI_ROADMAP.md) - Native app implementation (5 weeks)
- ⚙️ [Batch Automation](docs/AUTOMATION_ROADMAP.md) - Task processing pipeline

### Development Guides
- 🤖 [Agent Guidelines](docs/AI_AGENT_GUIDELINES.md) - Collaboration protocols for AI agents
- 🛠️ [Integration Guide](docs/GAME_LEARNING_INTEGRATION.md) - Developer implementation guide
- 📖 [Full Documentation Index](docs/INDEX.md) - Complete guide to all docs

## Open Source
This project is licensed under the MIT License. Contributions are welcome!

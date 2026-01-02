# AAS MASTER ROADMAP

This document tracks the high-level milestones and strategic evolution of the Aaroneous Automation Suite (AAS).

## 🎯 Current Milestone: Phase 1 - The Shared Brain
- [x] Initialize AAS Repository
- [x] Secure Key Infrastructure
- [x] Bootstrap Shared Brain (.sixthrules)
- [x] Implement Resilient Config
- [x] Build gRPC Bridge (Protos Generated)
- [x] Implement FCFS Handoff Protocol (Local-First)

## 🚀 Future Milestones

### Phase 2: Resilient Core & IPC
- [ ] Implement Pydantic RCS (Resilient Configuration System)
- [ ] Connect Linear API (Bi-directional Sync)
- [ ] Establish Policy Continuity (Project Maelstrom)
- [ ] **Agentic Workflows**: Integrate frameworks like `LangGraph` or `CrewAI` for autonomous goal decomposition.
- [ ] **Local LLM Support**: Add fallback to local models (Ollama/Llama.cpp) for privacy and offline use.

### Phase 3: Plugin Ecosystem & Intelligence
- [ ] Home Assistant Integration (Voice-to-Automation Pipeline)
- [ ] Onboard AI Assistant (CodeGPT Delegation)
- [ ] **Multi-Modal Vision Research**: GPT-4o/VLM integration for UI analysis in Maelstrom.
- [ ] **Autonomous SysAdmin**: Self-healing server monitoring in `home_server` plugin.

### Phase 4: Watch, Learn & Master
- [ ] Imitation Learning Plugin (Recorder/Player)
- [ ] **Reinforcement Learning (RL) Loop**: "Try and Master" training orchestrator.
- [ ] **Universal Game Adapter**: Standardized interface for controlling any windowed application.

### Phase 5: Developer Experience & Security
- [ ] **Node-Based Visual Scripting**: Visual flow editor for DeimosLang in `dev_studio`.
- [ ] **Zero-Trust Security**: mTLS for the gRPC bridge.
- [ ] **Decentralized Handoff**: Research local Git (Gitea) or decentralized protocols for artifacts.

## 📦 Consolidated Ecosystem (Migration from Legacy Repos)
- [ ] **AutoWizard101 Integration**: Migrate `HandoffTray` and `MaelstromBot.Server` into AAS Plugins.
- [ ] **Deimos-Wizard101 Integration**: Port `DeimosLang` VM and Questing logic to AAS Core.
- [ ] **DanceBot Integration**: Unify `Wizard101_DanceBot` assets and logic into AAS `game_manager`.

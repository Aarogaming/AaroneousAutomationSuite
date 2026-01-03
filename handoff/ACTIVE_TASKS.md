# AAS Active Task Board

This is the local source of truth for task delegation. AI actors claim tasks by updating the `Status` and `Assignee` columns.

## Active Tasks

| ID | Priority | Title | Depends On | Status | Assignee | Created | Updated |
|:---|:---|:---|:---|:---|:---|:---|:---|
| AAS-002 | High | Test FCFS Claiming | AAS-001 | Done | CodeGPT | 2026-01-02 | 2026-01-02 |
| AAS-113 | Medium | Build Unified Task Manager with Workspace Monitor | - | Done | GitHub Copilot | 2026-01-02 | 2026-01-02 |
| AAS-114 | High | Implement gRPC Task Broadcasting | AAS-113 | Done | Sixth | 2026-01-02 | 2026-01-03 |
| AAS-213 | High | Implement Live Event Stream (WebSockets) | AAS-113 | queued | - | 2026-01-02 | 2026-01-02 |
| AAS-214 | High | Scaffold Mission Control Dashboard | AAS-213 | queued | - | 2026-01-02 | 2026-01-02 |
| AAS-201 | Medium | Centralized Config Service | AAS-113 | queued | - | 2026-01-02 | 2026-01-02 |
| AAS-207 | High | Implement Multi-Modal Knowledge Graph | AAS-113 | queued | - | 2026-01-02 | 2026-01-02 |
| AAS-208 | High | Implement Agentic Self-Healing Protocol | AAS-207 | queued | - | 2026-01-02 | 2026-01-02 |
| AAS-220 | Medium | Create Plugin Test Suite | AAS-113 | queued | - | 2026-01-02 | 2026-01-02 |
| AAS-224 | Low | Implement Community Forge (Marketplace) | AAS-214 | queued | - | 2026-01-02 | 2026-01-02 |
| AAS-104 | High | Integrate OpenAI Agents SDK | AAS-003 | queued | - | 2026-01-02 | 2026-01-02 |
| AAS-105 | Medium | Build ChatKit Agent Dashboard | AAS-104 | queued | - | 2026-01-02 | 2026-01-02 |
| AAS-110 | Medium | Integrate DevToys SDK Extensions | AAS-003 | queued | - | 2026-01-02 | 2026-01-02 |
| AAS-112 | Medium | Integrate ngrok Tunneling for Development | AAS-003 | queued | - | 2026-01-02 | 2026-01-02 |
| AAS-014 | Low | DanceBot Integration | AAS-012, AAS-013 | queued | - | 2026-01-02 | 2026-01-02 |
| AAS-109 | Medium | Integrate Penpot Design System | AAS-003 | queued | - | 2026-01-02 | 2026-01-02 |

## Task Details

### AAS-002: Test FCFS Claiming
- **Description**: Validate that the FCFS claiming system works correctly with multiple agents
- **Acceptance Criteria**:
    - [x] Multiple agents can claim tasks without conflicts
    - [x] Task board updates correctly when claimed
    - [x] Dependencies are respected during claiming
- **Status**: Done (CodeGPT)

### AAS-113: Build Unified Task Manager with Workspace Monitor
- **Description**: Create a unified interface for managing tasks across all systems (Linear, local, etc.)
- **Status**: Done (GitHub Copilot - 2026-01-02)
- **Acceptance Criteria**:
    - [x] Build task aggregation from multiple sources (HandoffManager + AutoBatcher + BatchProcessor)
    - [x] Create unified CLI for task operations (task_manager_cli.py)
    - [x] Integrate batch tracking and history
    - [x] Add methods for finding unbatched tasks
    - [x] Implement claim/complete/status operations
    - [x] Add task analytics and reporting (health summary)
    - [x] Add workspace file monitoring (Implemented via `WorkspaceCoordinator`)
- **Implementation**:
    - Created `core/handoff/task_manager.py` - Unified TaskManager class
    - Created `scripts/task_manager_cli.py` - CLI interface
    - Created `core/handoff/workspace_coordinator.py` - Workspace monitoring and hygiene
    - Integrated HandoffManager, AutoBatcher, and BatchProcessor
    - Added batch tracking with history persistence
    - Implemented FCFS claiming with batch awareness
    - Added comprehensive status and health reporting

### AAS-114: Implement gRPC Task Broadcasting
- **Description**: Enhance the IPC Bridge to broadcast task updates to all connected clients in real-time.
- **Dependencies**: AAS-113 (Unified Task Manager)
- **Acceptance Criteria**:
    - [x] Update `bridge.proto` with `SubscribeToTasks` rpc
    - [x] Implement pub/sub logic in `BridgeService`
    - [x] Update `TaskManager` to trigger broadcasts on task state changes
    - [x] Add client-side listener in CLI

### AAS-213: Implement Live Event Stream (WebSockets)
- **Description**: Real-time action broadcasting from clients to Hub via WebSockets.
- **Dependencies**: AAS-113
- **Acceptance Criteria**:
    - [ ] Set up WebSocket server in FastAPI Hub
    - [ ] Integrate WebSocket client into `PluginBase`
    - [ ] Broadcast `ACTION_EXECUTED` and `STATE_CHANGED` events
    - [ ] Implement event filtering by client ID

### AAS-214: Scaffold Mission Control Dashboard
- **Description**: Central web UI for real-time monitoring and management.
- **Dependencies**: AAS-213
- **Acceptance Criteria**:
    - [ ] Scaffold React + Vite + Tailwind frontend
    - [ ] Implement Fleet Overview grid
    - [ ] Add Live Console with WebSocket feed
    - [ ] Integrate Task Board Kanban view

### AAS-201: Centralized Config Service
- **Description**: Secure, DB-backed vault for multi-client configuration.
- **Dependencies**: AAS-113
- **Acceptance Criteria**:
    - [ ] Implement Fernet encryption for secrets
    - [ ] Add `GetConfig` gRPC endpoint
    - [ ] Create Dashboard settings page for config management
    - [ ] Implement client-side config sync on startup

### AAS-207: Implement Multi-Modal Knowledge Graph
- **Description**: Vector-backed memory system for error/solution patterns.
- **Dependencies**: AAS-113
- **Acceptance Criteria**:
    - [ ] Integrate `sqlite-vss` for vector search
    - [ ] Implement `KnowledgeNode` and `KnowledgeEdge` models
    - [ ] Add semantic search API to `KnowledgeManager`
    - [ ] Implement auto-indexing for completed tasks

### AAS-208: Implement Agentic Self-Healing Protocol
- **Description**: Automated recovery from environment and UI failures.
- **Dependencies**: AAS-207
- **Acceptance Criteria**:
    - [ ] Implement `SelfHealingManager` orchestration
    - [ ] Add `capture_diagnostic_pack` to `WorkspaceCoordinator`
    - [ ] Integrate AI-based analysis for new error patterns
    - [ ] Implement `safe_execute` wrapper in `PluginBase`

### AAS-220: Create Plugin Test Suite
- **Description**: Pytest framework with `MockAdapter` for headless testing.
- **Dependencies**: AAS-113
- **Acceptance Criteria**:
    - [ ] Implement `MockAdapter` for game state simulation
    - [ ] Create standard pytest fixtures for Hub and Plugins
    - [ ] Add example tests for core plugins
    - [ ] Integrate test runner into CLI

### AAS-224: Implement Community Forge (Marketplace)
- **Description**: Plugin registry with GitHub/Steam integration.
- **Dependencies**: AAS-214
- **Acceptance Criteria**:
    - [ ] Define `aas-plugin.json` manifest standard
    - [ ] Implement `aas forge install` CLI command
    - [ ] Add Marketplace tab to Dashboard
    - [ ] Implement GitHub/Steam platform adapters

### AAS-014: DanceBot Integration
- **Description**: Integrate the Wizard101 DanceBot into the AAS plugin ecosystem
- **Dependencies**: AAS-012 (AutoWizard101 Migration), AAS-013 (Deimos-Wizard101 Port)
- **Acceptance Criteria**:
    - [ ] Create `plugins/dance_bot/` module
    - [ ] Port dance game logic from standalone repo
    - [ ] Integrate with IPC bridge for Maelstrom commands
    - [ ] Add CLI commands for dance bot operations

### AAS-104: Integrate OpenAI Agents SDK
- **Description**: Integrate the new OpenAI Agents SDK for enhanced agentic capabilities
- **Dependencies**: AAS-003 (Pydantic RCS)
- **Priority**: High
- **Acceptance Criteria**:
    - [ ] Install and configure OpenAI Agents SDK
    - [ ] Create agent wrappers in `plugins/ai_assistant/`
    - [ ] Implement agent handoff protocols
    - [ ] Add agent state persistence

### AAS-105: Build ChatKit Agent Dashboard
- **Description**: Create a web dashboard for monitoring and managing AI agents
- **Dependencies**: AAS-104 (OpenAI Agents SDK)
- **Acceptance Criteria**:
    - [ ] Set up FastAPI backend
    - [ ] Create React/Vue frontend
    - [ ] Display agent status and task progress
    - [ ] Add real-time updates via WebSockets

### AAS-109: Integrate Penpot Design System
- **Description**: Integrate Penpot for design system management
- **Dependencies**: AAS-003 (Pydantic RCS)
- **Acceptance Criteria**:
    - [ ] Set up Penpot instance or cloud connection
    - [ ] Create design tokens synchronization
    - [ ] Integrate with dev_studio plugin

### AAS-110: Integrate DevToys SDK Extensions
- **Description**: Add DevToys-style utilities to the dev_studio plugin
- **Dependencies**: AAS-003 (Pydantic RCS)
- **Acceptance Criteria**:
    - [ ] Implement JSON formatter/validator
    - [ ] Add base64 encoder/decoder
    - [ ] Add regex tester
    - [ ] Create utility CLI commands

### AAS-112: Integrate ngrok Tunneling for Development
- **Description**: Add ngrok support for exposing local services
- **Dependencies**: AAS-003 (Pydantic RCS)
- **Acceptance Criteria**:
    - [ ] Create ngrok plugin wrapper
    - [ ] Add tunnel management commands
    - [ ] Integrate with IPC and Home Assistant plugins
    - [ ] Add configuration for tunnel persistence

### AAS-212: Implement Agent Handoff Protocol
- **Description**: Standardize context sharing between specialized AI agents.
- **Dependencies**: AAS-113
- **Acceptance Criteria**:
    - [ ] Define `HandoffObject` schema
    - [ ] Implement `AgentCollaborationManager.relay_handoff()`
    - [ ] Add handoff history tracking in DB

### AAS-223: Automated Documentation Generator
- **Description**: Keep `INDEX.md` and API docs in sync with code changes.
- **Dependencies**: AAS-113
- **Acceptance Criteria**:
    - [ ] Implement docstring parser
    - [ ] Generate markdown files for all core managers
    - [ ] Add CLI command `aas docs generate`

### AAS-209: Semantic Error Clustering
- **Description**: Group similar failures in the DB to identify systemic bugs.
- **Dependencies**: AAS-207
- **Acceptance Criteria**:
    - [ ] Implement error pattern extraction
    - [ ] Add clustering logic using vector embeddings
    - [ ] Create Dashboard view for error clusters

### AAS-211: Automated Task Decomposition
- **Description**: Use LangGraph to break complex goals into actionable DAGs.
- **Dependencies**: AAS-113
- **Acceptance Criteria**:
    - [ ] Implement decomposition graph in `core/agents/`
    - [ ] Add sub-task generation with dependency mapping
    - [ ] Integrate with `TaskManager.add_task()`

### AAS-215: Visual Scripting Editor (dev_studio)
- **Description**: Node-based workflow builder in the Dashboard.
- **Dependencies**: AAS-214
- **Acceptance Criteria**:
    - [ ] Integrate React Flow into Dashboard
    - [ ] Implement node registry (Action, Logic, Trigger)
    - [ ] Add graph-to-Python compiler

### AAS-221: Multi-Game Adapter (Roblox/Minecraft)
- **Description**: Generalize the `game_manager` for other platforms.
- **Dependencies**: AAS-113
- **Acceptance Criteria**:
    - [ ] Create `RobloxAdapter` and `MinecraftAdapter`
    - [ ] Standardize window detection for non-Win32 games
    - [ ] Implement basic input injection for new platforms

### AAS-222: Home Assistant Voice Bridge
- **Description**: Trigger automations via voice commands.
- **Dependencies**: AAS-113
- **Acceptance Criteria**:
    - [ ] Set up voice intent parser
    - [ ] Map intents to AAS plugin methods
    - [ ] Integrate with Home Assistant Assist

### AAS-301: Swarm Orchestration Protocol
- **Description**: Implement multi-agent consensus and red-teaming.
- **Dependencies**: AAS-212
- **Acceptance Criteria**:
    - [ ] Implement `SwarmManager` for agent orchestration
    - [ ] Add consensus voting logic
    - [ ] Implement red-team agent for code verification

### AAS-302: Vision-to-Code Generator
- **Description**: Automatically generate adapters by analyzing game windows.
- **Dependencies**: AAS-207
- **Acceptance Criteria**:
    - [ ] Implement UI element detection via Vision API
    - [ ] Generate `GameAdapter` boilerplate from detection results
    - [ ] Add automated verification of generated code

### AAS-303: Behavioral Cloning (Ghost Mode)
- **Description**: Train RL agents by watching human gameplay.
- **Dependencies**: AAS-113
- **Acceptance Criteria**:
    - [ ] Implement input recorder in `imitation_learning` plugin
    - [ ] Add state-action pair dataset generation
    - [ ] Train base model using behavioral cloning

### AAS-304: Federated Learning Mesh
- **Description**: Securely share healing strategies across decentralized Hubs.
- **Dependencies**: AAS-207
- **Acceptance Criteria**:
    - [ ] Implement Hub-to-Hub gRPC communication
    - [ ] Add anonymized error/solution sharing
    - [ ] Implement local model fine-tuning from shared data

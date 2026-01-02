# AAS Evolution Plan: Elevating the Suite

This document outlines the strategic roadmap to evolve the Aaroneous Automation Suite (AAS) from a robust automation hub into a world-class, autonomous AI ecosystem.

## 1. AI & Intelligence Evolution
### 🧠 Agentic Workflows
*   **Goal:** Move from "Prompt/Response" to "Autonomous Agents."
*   **Implementation:** Integrate frameworks like `LangGraph` or `CrewAI` within the `ai_assistant` plugin. This allows AAS to break down complex goals (e.g., "Optimize my home server energy usage") into sub-tasks and execute them without human intervention.
*   **Local LLM Support:** Add a fallback to local models (via Ollama or Llama.cpp) to ensure the suite remains functional and private even without an internet connection.

### 👁️ Multi-Modal Vision Research
*   **Goal:** Allow the AI to "see" and research games visually.
*   **Implementation:** Use GPT-4o or local Vision-Language Models (VLMs) to analyze screenshots from Maelstrom. The AI can then "research" a new mini-game by looking at the UI elements and inferring the rules.

## 2. Automation & Learning Evolution
### 🎮 Reinforcement Learning (RL) Loop
*   **Goal:** Beyond "Watch and Learn," implement "Try and Master."
*   **Implementation:** Build a training orchestrator that uses the `imitation_learning` data as a baseline, then runs the game in a "Sandbox" mode where the AI explores different actions to maximize a reward (e.g., high score, gold earned).

### 🔌 Universal Game Adapter
*   **Goal:** Play *any* game, not just Wizard101.
*   **Implementation:** Create a standardized `GameAdapter` interface. New games can be added by providing a "Vision Map" (UI coordinates) and an "Input Map" (Keybindings), allowing AAS to control any windowed application.

## 3. Home & Server Evolution
### 🎙️ Voice-to-Automation Pipeline
*   **Goal:** Control AAS and Maelstrom via voice.
*   **Implementation:** Integrate with Home Assistant's "Assist" pipeline. You could say, "Hey AAS, start the Halfang farm on p1," and the Hub will route the command through the IPC bridge.

### 🛠️ Autonomous SysAdmin
*   **Goal:** A self-healing home server.
*   **Implementation:** The `home_server` plugin should evolve to monitor service health (Docker, Databases). If a service fails, AAS researches the error log internally and performs a safe restart or configuration fix.

## 4. Developer & UX Evolution
### 🎨 Node-Based Visual Scripting
*   **Goal:** Make DeimosLang accessible to everyone.
*   **Implementation:** Build a visual flow editor in the `dev_studio` where users can drag-and-drop logic blocks (e.g., "If Health < 20%" -> "Use Potion") to generate DeimosLang scripts.

### 🛡️ Zero-Trust Security
*   **Goal:** Enterprise-grade security for an open-source project.
*   **Implementation:** Implement mTLS (mutual TLS) for the gRPC bridge to ensure that only authorized AAS Hubs can send commands to Maelstrom instances.

## 5. Handoff & Governance Evolution
### 🛰️ Decentralized Handoff
*   **Goal:** Remove reliance on third-party cloud providers.
*   **Implementation:** Research using a local Git server (Gitea) or a decentralized protocol for storing handoff artifacts, ensuring your "Shared Brain" is 100% owned by you.

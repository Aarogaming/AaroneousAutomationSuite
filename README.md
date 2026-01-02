# Aaroneous Automation Suite (AAS)

## Overview
Aaroneous Automation Suite is an open-source, multi-purpose automation ecosystem. It is designed to act as a central hub for high-performance game management, home automation, and AI-assisted research.

## Unified Ecosystem Architecture
- **AAS Hub (Python):** The central orchestrator for plugins, AI assistance, and home server management.
- **Project Maelstrom (C#):** Located in `game_manager/maelstrom`, handling memory-level state and UI automation.
- **Deimos (Python):** Located in `core/deimos`, providing advanced logic and questing capabilities.
- **DanceBot (Python):** Located in `plugins/dance_bot`, specialized automation for game mini-games.

## Key Features
- **Resilient Configuration:** Type-safe validation with Pydantic and secure local secret management.
- **Autonomous Handoff Protocol (AHP):** A seamless development loop between Linear, ChatGPT 5.2 Pro, and Sixth.
- **Onboard AI Assistant:** Integrated GPT-5.2 Pro for real-time strategy and code generation.
- **Watch and Learn:** Imitation learning plugin to record and automate player actions in any game.
- **AAS Dev Studio:** Internal code editor and terminal for self-building capabilities.

## Getting Started
1. Install dependencies: `pip install -r requirements.txt`
2. Configure your local environment in `.env` (OpenAI API Key, etc.)
3. Start the Hub: `python core/main.py`

## Open Source
This project is licensed under the MIT License. Contributions are welcome!

# Workspace Context: Aaroneous Automation Suite (AAS)

## Overview
A multi-purpose automation ecosystem designed for high-performance game management (Project Maelstrom) and general-purpose automation (Home Assistant, Home Server, AI Research).

## Module Map
- `core/`: AAS Python Hub (Plugin Loader, IPC Orchestrator).
- `plugins/`: Dynamic extensions (Home Assistant, Server Monitoring, Research Agent).
- `game_manager/`: Project Maelstrom (C# WinForms, OCR, Memory-level game state).
- `scripts/`: DeimosLang automation scripts and VM logic.
- `artifacts/`: Handoff reports, snapshots, and audit trails.

## Local Commands
- **AAS Hub:** `python core/main.py` (Requires `requirements.txt`)
- **Maelstrom:** `dotnet run --project ProjectMaelstrom/ProjectMaelstrom.csproj`
- **Tests (AAS):** `pytest`
- **Tests (Maelstrom):** `dotnet test ProjectMaelstrom/ProjectMaelstrom.Tests`
- **Handoff Loop:** `./scripts/coop_loop.ps1`

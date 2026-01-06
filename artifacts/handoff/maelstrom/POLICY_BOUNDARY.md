# Maelstrom Policy Boundary

## Overview
Project Maelstrom operates under a strict governance model to ensure high performance and system stability.

## Core Principles
1. **Performance First**: All automation logic must minimize CPU and memory overhead.
2. **Safety**: OCR and Memory-level interactions must include validation checks to prevent game state corruption.
3. **Auditability**: Every action taken by an agent must be logged.

## Agent Constraints
- Agents cannot modify the core gRPC bridge without approval from Sixth.
- Agents must use Git worktrees for all task execution.
- Agents must run the full test suite before submitting changes.

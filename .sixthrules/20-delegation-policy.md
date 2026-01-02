# Delegation & Governance Policy v1.0

## Overview
This policy defines how tasks are delegated between different AI actors and human operators within the AAS ecosystem.

## AI Actors
- **Sixth:** Primary architect and system engineer. Handles core AAS development and complex cross-module integration.
- **ChatGPT-5.2:** High-level strategic planning and research. Used for brainstorming and complex logic verification.
- **CodeGPT:** Specialized in targeted code generation, refactoring, and unit test creation. Ideal for boilerplate and repetitive implementation tasks.

## Delegation Criteria
- **Sixth** should be used for:
    - Architectural changes.
    - Security-sensitive code.
    - Complex debugging across Python and C#.
- **CodeGPT** should be used for:
    - Implementing well-defined interfaces.
    - Writing unit tests for existing modules.
    - Refactoring code for style and consistency.
- **ChatGPT-5.2** should be used for:
    - Drafting documentation.
    - Researching new technologies (e.g., VLMs, RL).
    - High-level project roadmap planning.

## Handoff Protocol
All delegations must follow the [Handoff Service Contract](./10-handoff-contract.md).
1. Task is queued in Linear.
2. Actor claims the task.
3. Actor provides periodic progress events.
4. Actor submits artifacts and marks task as done.

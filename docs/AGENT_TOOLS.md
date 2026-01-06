# AAS Agent Integration & Isolation Strategy

## Overview
To enable high-throughput, parallel task execution, AAS integrates background coding agents (Aider, Claude Code, Cline) using Git Worktrees for isolation. This prevents merge conflicts and allows multiple agents to work on different tasks simultaneously.

## Supported Agents
- **Aider**: Best for repetitive tasks, migrations, and documentation. Can run locally with Ollama.
- **Claude Code**: High-performance cloud agent for complex architectural changes.
- **Cline**: Interactive VS Code agent for UI and refinement.

## Worktree Isolation Strategy
Every task claimed by a background agent MUST operate in a dedicated Git worktree.

### Workflow:
1. **Claim Task**: Agent claims task in `handoff/ACTIVE_TASKS.md`.
2. **Create Worktree**:
   ```bash
   git worktree add ../worktrees/AAS-XXX task-branch-name
   ```
3. **Execute**: Agent runs within the worktree directory.
4. **Verify**: Run tests within the worktree.
5. **Merge**: Push branch and create PR (or merge to main if autonomous).
6. **Cleanup**:
   ```bash
   git worktree remove ../worktrees/AAS-XXX
   ```

## Aider + Ollama Setup
AAS is pre-configured to use Aider with local Ollama models.
- **Config**: `.aider.conf.yml`
- **Command**: `aider --model ollama/llama3`

## Registering Agents
Agents should be registered via `HandoffManager.register_background_agent()` to track active sessions and resource usage.

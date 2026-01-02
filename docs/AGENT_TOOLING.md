# Agent Tooling & Orchestration Guide

## Overview

The Aaroneous Automation Suite (AAS) is designed to work seamlessly with multiple AI coding agents, enabling collaborative development through the **Autonomous Handoff Protocol (AHP)**. This guide covers all supported agents, their capabilities, and best practices for coordination.

## Agent Ecosystem

### Primary Agents

#### 1. **Codex CLI** (OpenAI)
**Type:** Command-line coding agent  
**Models:** GPT-4, GPT-4 Turbo, GPT-5.2 Pro  
**Strengths:** Complex refactoring, architectural planning, multi-file edits

**Installation:**
```bash
npm install -g @openai/codex-cli
# or
pip install openai-codex-cli
```

**Usage Modes:**
- **Interactive Mode:** `codex` - Opens interactive session
- **Execute Mode:** `codex -e "task description"` - One-shot task execution
- **Approval Modes:**
  - `--auto-approve` - Execute without confirmation (use with caution)
  - `--review` - Show changes before applying (default)
  - `--dry-run` - Show changes without applying

**Windows Support:**
```powershell
# PowerShell execution
codex -e "Add error handling to combat_new.py"

# With approval
codex --review -e "Refactor spell casting logic"
```

**Configuration:**
```bash
# Set API key
export OPENAI_API_KEY="your-key-here"

# Configure model
codex config set model gpt-4-turbo

# Set workspace
codex config set workspace /path/to/AaroneousAutomationSuite
```

**Best Practices:**
- Use for large-scale refactoring (5+ files)
- Leverage architectural planning capabilities
- Review changes before auto-approval in critical code
- Use `--dry-run` for exploratory analysis

---

#### 2. **GitHub Copilot** (Microsoft)
**Type:** IDE-integrated assistant + chat + CLI  
**Models:** GPT-4 based (proprietary)  
**Strengths:** Real-time code completion, inline suggestions, workspace-aware chat

**Integration:**
- **VS Code Extension:** Built-in chat and inline suggestions
- **Copilot CLI:** `gh copilot suggest` and `gh copilot explain`
- **Workspace Context:** Automatically indexes codebase

**Usage:**
```bash
# Suggest shell command
gh copilot suggest "find all Python files modified in last week"

# Explain code
gh copilot explain "core/handoff/manager.py"

# In VS Code: Ctrl+I or Cmd+I for inline chat
```

**Coordination with AAS:**
- Reads `.github/copilot-instructions.md` for project context
- Understands AAS architecture via workspace indexing
- Can create/modify files, run tests, debug issues

---

#### 3. **Claude Code** (Anthropic)
**Type:** Desktop app coding agent  
**Models:** Claude 3.5 Sonnet, Claude Opus  
**Strengths:** Long context (200K tokens), nuanced reasoning, ethical considerations

**Setup:**
```bash
# Install Claude Desktop (includes Code)
# Download from: https://claude.ai/desktop

# Configure MCP servers (see README.md Linear MCP section)
```

**Features:**
- **File Editing:** Direct file read/write with user approval
- **Terminal Access:** Run commands in workspace
- **MCP Integration:** Linear, GitHub, filesystem access
- **Conversation Memory:** Retains context across sessions

**Best Use Cases:**
- Complex feature implementation (requires deep context)
- Architecture discussions and planning
- Code review with ethical/safety considerations

---

#### 4. **Sixth** (Custom Agent)
**Type:** Specialized AAS agent  
**Models:** Configurable (OpenAI, Anthropic, local)  
**Strengths:** AAS-specific workflows, Linear integration, task decomposition

**Configuration:**
Located in `.env`:
```bash
SIXTH_ENABLED=true
SIXTH_MODEL=gpt-4-turbo
SIXTH_LINEAR_SYNC=true
```

**Capabilities:**
- Task claiming from `handoff/ACTIVE_TASKS.md`
- Autonomous subtask decomposition
- Linear issue creation/updates
- Project Maelstrom coordination

**Usage:**
```bash
# Start Sixth in terminal
python core/main.py sixth --claim-task AAS-025

# Interactive mode
python core/main.py sixth --interactive
```

---

#### 5. **Cline** (VS Code Extension)
**Type:** Agentic coding assistant  
**Models:** OpenAI, Anthropic, Ollama (configurable)  
**Strengths:** Multi-step task execution, file operations, terminal commands

**Installation:**
```bash
# Via VS Code Extensions Marketplace
code --install-extension saoudrizwan.claude-dev

# Or search "Cline" in VS Code Extensions
```

**Features:**
- **Task Mode:** Execute multi-step coding tasks
- **Chat Mode:** Conversational coding assistance
- **Tool Use:** File editing, terminal commands, web search
- **Context Management:** Automatically includes relevant files

**Configuration:**
```json
// .vscode/settings.json
{
  "cline.apiProvider": "openai",
  "cline.model": "gpt-4-turbo",
  "cline.maxTokens": 8000,
  "cline.autoApprove": false
}
```

---

#### 6. **Aider** (Terminal-Based)
**Type:** Pair programming CLI agent  
**Models:** GPT-4, Claude, local models via Ollama  
**Strengths:** Git-aware editing, test-driven development, commit generation

**Installation:**
```bash
pip install aider-chat
```

**Usage:**
```bash
# Start aider in repository
aider

# Add files to context
aider core/handoff/manager.py core/config/manager.py

# Specify model
aider --model gpt-4-turbo

# Use local model
aider --model ollama/codellama

# Git integration
aider --auto-commits  # Auto-commit successful changes
```

**Best Practices:**
- Add only files you need (context efficiency)
- Use `--model` flag to switch between models
- Leverage `--auto-commits` for atomic changes
- Combine with `--watch` for continuous development

---

#### 7. **CodeGPT** (IDE Extension)
**Type:** Multi-IDE coding assistant  
**Models:** OpenAI, Anthropic, Azure, local  
**Strengths:** Cross-IDE support, custom agents, prompt templates

**Supported IDEs:**
- VS Code
- JetBrains (IntelliJ, PyCharm, WebStorm)
- Neovim

**Features:**
- Inline code generation
- Custom agent personas
- Prompt template library
- Model switching

---

### Local/Offline Agents

#### 8. **ARGO** (Task Decomposition Agent)
**Type:** Native Python agent runtime  
**Models:** Ollama (Mistral, CodeLlama, etc.)  
**Strengths:** Autonomous task decomposition, memory persistence

**Setup:** See [Local Agent Framework Integration](docs/LOCAL_AGENTS.md)

**Usage:**
```python
from core.handoff.agents import ARGOClient

argo = ARGOClient(model_endpoint="http://localhost:11434")
result = await argo.execute_goal("Implement spell damage calculation")
```

---

#### 9. **Observer AI** (Vision-Based Agent)
**Type:** Screen observation and automation  
**Models:** GPT-4 Vision, Claude 3 Vision  
**Strengths:** UI/UX testing, visual debugging, screenshot analysis

**Installation:**
```bash
pip install observer-ai
```

**Use Cases:**
- Automated UI testing (Project Maelstrom)
- Visual regression detection
- Screenshot-based debugging

---

## Agent Coordination Patterns

### Pattern 1: Sequential Handoff (FCFS)
**Use When:** Multiple agents working on independent tasks

```
1. Copilot claims AAS-025 → Implements feature
2. Copilot marks Done → Creates handoff artifact
3. Sixth claims AAS-026 → Continues next task
```

**Implementation:**
```bash
# Copilot claims task
python core/main.py claim AAS-025

# Sixth monitors task board
python core/main.py board --filter status:queued
```

---

### Pattern 2: Parallel Collaboration
**Use When:** Large tasks requiring multiple specializations

```
Task: Refactor combat system (AAS-050)
├─ Copilot: Core logic refactoring
├─ Sixth: Linear issue tracking
├─ Cline: Test suite creation
└─ Aider: Git commit management
```

**Coordination:**
- Use `handoff/ACTIVE_TASKS.md` for task board
- Create subtasks in Linear for each agent
- Use Git branches for isolated work

---

### Pattern 3: Review Chain
**Use When:** High-stakes changes requiring validation

```
1. Cline implements feature → Creates PR
2. Copilot reviews code → Suggests improvements
3. Claude Code evaluates architecture → Approves/requests changes
4. Aider applies final polish → Merges PR
```

---

### Pattern 4: Research → Implementation → Testing
**Use When:** New feature development from scratch

```
Phase 1: Research (Claude Code)
├─ Explore existing patterns
├─ Evaluate trade-offs
└─ Propose architecture

Phase 2: Implementation (Copilot/Cline)
├─ Core functionality
├─ Error handling
└─ Documentation

Phase 3: Testing (Aider)
├─ Unit tests
├─ Integration tests
└─ Git commits with test results
```

---

## Configuration Files

### 1. `.github/copilot-instructions.md`
**Purpose:** Provide project context to GitHub Copilot

**Key Sections:**
- Project overview (AAS architecture)
- Core components (RCS, AHP, IPC Bridge, Plugin System)
- Developer workflows (setup, code quality, proto generation)
- Project-specific conventions (branching, commits, error handling)

**Update When:**
- New major feature added
- Architecture changes
- Convention updates

---

### 2. `handoff/ACTIVE_TASKS.md`
**Purpose:** Local source of truth for task delegation

**Structure:**
```markdown
| Task ID | Priority | Title | Dependencies | Status | Assignee | Created | Updated |
|---------|----------|-------|--------------|--------|----------|---------|---------|
| AAS-025 | High     | ...   | AAS-007      | In Progress | Sixth | ... | ... |
```

**Agent Usage:**
- **Read:** Check available tasks (`status:queued`)
- **Write:** Claim tasks (change status to `In Progress`, add assignee)
- **Complete:** Mark `Done`, create completion report

---

### 3. `.env`
**Purpose:** Environment configuration for all agents

**Agent-Specific Variables:**
```bash
# OpenAI (Codex CLI, CodeGPT, Aider)
OPENAI_API_KEY=sk-...

# Anthropic (Claude Code, Cline)
ANTHROPIC_API_KEY=sk-ant-...

# GitHub (Copilot)
GITHUB_TOKEN=ghp_...

# Linear (Sixth, Copilot)
LINEAR_API_KEY=lin_api_...
LINEAR_TEAM_ID=...

# Ollama (ARGO, Aider)
OLLAMA_URL=http://localhost:11434

# Sixth Configuration
SIXTH_ENABLED=true
SIXTH_MODEL=gpt-4-turbo
SIXTH_LINEAR_SYNC=true
```

---

## Best Practices

### 1. Task Claiming Protocol
✅ **DO:**
- Check dependencies before claiming (`Dependencies` column)
- Update status to `In Progress` immediately
- Add your agent name to `Assignee` column
- Create artifact directory (`artifacts/handoff/<task-id>/`)

❌ **DON'T:**
- Claim tasks with unmet dependencies
- Work on tasks claimed by other agents
- Forget to update task board when starting

---

### 2. Communication & Handoff
✅ **DO:**
- Create completion reports in `artifacts/handoff/reports/<task-id>/`
- Document blockers in Linear issues
- Use Git commit messages with task IDs: `feat(AAS-025): Add task decomposition`
- Include context in handoff artifacts

❌ **DON'T:**
- Leave incomplete work without status update
- Delete handoff artifacts created by other agents
- Merge PRs without review (use Review Chain pattern)

---

### 3. Model Selection
**Use GPT-4 Turbo When:**
- Fast iteration needed
- Cost is a factor
- Task is well-defined

**Use GPT-5.2 Pro When:**
- Complex reasoning required
- Multi-step planning needed
- Architectural decisions involved

**Use Claude 3.5 Sonnet When:**
- Long context essential (200K tokens)
- Nuanced understanding needed
- Ethical considerations important

**Use Local Models (Ollama) When:**
- Privacy is critical
- Offline operation required
- Cost must be zero

---

### 4. Context Management
**Strategies:**
- **Workspace Indexing:** Let Copilot/Claude Code index full workspace
- **Selective Context:** Aider/Cline - add only relevant files
- **Semantic Search:** Use `semantic_search` tool for large codebases
- **Documentation:** Keep `docs/` updated for agent reference

**Context Limits:**
| Agent | Context Window | Strategy |
|-------|----------------|----------|
| GPT-4 | 128K tokens | Workspace indexing |
| GPT-5.2 Pro | 200K tokens | Full project context |
| Claude 3.5 | 200K tokens | Document-heavy tasks |
| Codellama (7B) | 4K tokens | Focused file editing |
| Mistral (7B) | 8K tokens | Single-file tasks |

---

### 5. Error Handling
**When Agent Fails:**
1. Check `artifacts/handoff/reports/HEALTH_REPORT.md`
2. Review Linear issues for error reports
3. Use `handoff.report_event(task_id, "error", message)` to escalate
4. If critical: Update task status to `blocked`, add blocker note

**Common Issues:**
- **API Rate Limits:** Switch to local model or wait
- **Context Overflow:** Reduce files in context, use summaries
- **Dependency Conflicts:** Check `Dependencies` column, wait for prerequisite
- **Git Conflicts:** Use Aider with `--auto-commits` for atomic changes

---

## Advanced Features

### 1. Multi-Agent Orchestration (ARGO + n8n)
**Scenario:** Automate combat log analysis pipeline

```yaml
# n8n workflow: combat-analysis-pipeline
Trigger: New file in artifacts/combat_logs/
├─ Step 1: Parse log (Python Code node)
├─ Step 2: ARGO task decomposition
│   └─ Subtask 1: Identify inefficiencies
│   └─ Subtask 2: Suggest optimizations
│   └─ Subtask 3: Generate report
├─ Step 3: Create Linear issue (if issues found)
└─ Step 4: Notify via Discord
```

**Setup:**
See [Local Agent Framework Integration](docs/LOCAL_AGENTS.md) for n8n configuration.

---

### 2. Knowledge-Augmented Agents (AnythingLLM)
**Scenario:** Agent needs project documentation context

```python
from core.handoff.knowledge import AnythingLLMClient

# Query AAS documentation
knowledge = AnythingLLMClient()
answer = await knowledge.query(
    workspace_id="aas-documentation",
    question="How does the IPC bridge work with Project Maelstrom?"
)

# Use in agent prompt
agent_prompt = f"Context: {answer.text}\n\nTask: Implement IPC feature..."
```

---

### 3. Continuous Development (Aider + Watch Mode)
**Scenario:** Real-time code refinement

```bash
# Start aider with watch mode
aider --watch --auto-commits core/handoff/manager.py

# Make change request
> "Add retry logic to claim_next_task method"

# Aider implements, tests, commits automatically
# Continue iterating without manual commits
```

---

## Troubleshooting

### Issue: Agent Can't Find Files
**Solution:**
```bash
# Rebuild workspace index
gh copilot index rebuild

# For Cline/Claude Code: Restart agent
# For Aider: Add files explicitly
aider core/handoff/*.py
```

---

### Issue: Linear Sync Failing
**Solution:**
```bash
# Verify Linear configuration
python scripts/verify_linear.py

# Check team ID matches
grep LINEAR_TEAM_ID .env

# Expected output: c29f99c3-3f99-45b6-8be2-2c606808115a
```

---

### Issue: Agent Produces Incorrect Code
**Solution:**
1. **Add Context:** Include related files, documentation
2. **Refine Prompt:** Be more specific about requirements
3. **Switch Model:** Try GPT-4 → GPT-5.2 or Claude 3.5
4. **Review Chain:** Have another agent review output

---

### Issue: Multiple Agents Claim Same Task
**Prevention:**
- Always check `Status` column before claiming
- Use `git pull` to sync task board before claiming
- Implement file locking (future enhancement)

**Resolution:**
1. First agent to update task board owns task
2. Second agent should check Git history: `git log handoff/ACTIVE_TASKS.md`
3. Second agent abandons claim, selects different task

---

## Integration Examples

### Example 1: Copilot + Sixth Collaboration
```bash
# Terminal 1: Copilot (you)
# Claim task, implement feature
python core/main.py claim AAS-050
# ... implement combat refactoring ...
python core/main.py complete AAS-050

# Terminal 2: Sixth (autonomous)
python core/main.py sixth --claim-task AAS-051
# Sixth detects AAS-050 completion, claims next task
# Creates Linear issue for tracking
```

---

### Example 2: Cline + Aider Pair Programming
```bash
# Step 1: Cline implements feature (VS Code)
# Ctrl+I: "Implement spell damage calculation with buffs"

# Step 2: Aider adds tests (terminal)
aider core/deimos/src/combat_new.py --test-cmd "pytest tests/test_combat.py"
> "Add unit tests for spell damage calculation"

# Step 3: Aider auto-commits on success
# Commit message: "test: Add unit tests for spell damage calculation"
```

---

### Example 3: Claude Code Research → Codex CLI Implementation
```bash
# Phase 1: Claude Code (Desktop app)
# Research optimal architecture for plugin system
# Output: Detailed architecture document in artifacts/research/plugin_arch.md

# Phase 2: Codex CLI (terminal)
codex --review -e "Implement plugin system based on artifacts/research/plugin_arch.md"
# Codex reads architecture doc, implements across multiple files
# Review changes, approve
```

---

## Metrics & Monitoring

### Agent Performance Tracking
**Metrics:**
- Tasks completed per agent
- Average completion time
- Error rate (tasks requiring rework)
- FCFS fairness (no agent hoarding tasks)

**Monitoring:**
```bash
# View agent activity
python core/main.py board --stats

# Output:
# Copilot: 5 tasks completed, avg 2.3 hours
# Sixth: 8 tasks completed, avg 1.5 hours
# Cline: 3 tasks completed, avg 3.1 hours
```

---

### Task Board Health
**Indicators:**
- Queued tasks with unmet dependencies: **0** ✓
- In Progress tasks abandoned >24h: **0** ✓
- Blocked tasks without Linear issue: **0** ✓

**Health Check:**
```bash
python core/main.py health
# Checks task board, handoff artifacts, Linear sync
```

---

## Future Enhancements

### Planned Features
- **Agent Profiles:** Define agent capabilities in `agents.yaml`
- **Task Routing:** Automatically suggest tasks based on agent strengths
- **Conflict Resolution:** Automatic merge conflict handling
- **Performance Benchmarking:** Track agent velocity over time
- **Cost Tracking:** Monitor API usage per agent

### Experimental
- **Voice-to-Agent:** Trigger agents via Home Assistant voice commands
- **Visual Agents:** UI testing with Observer AI + Playwright
- **Swarm Mode:** Multiple agents work on single task collaboratively

---

## References

- [AAS Project Overview](README.md)
- [Autonomous Handoff Protocol](AGENTS.md)
- [Local Agent Framework Integration](docs/LOCAL_AGENTS.md)
- [Linear Integration Guide](.github/LINEAR_INTEGRATION.md)
- [GitHub Copilot Documentation](https://docs.github.com/en/copilot)
- [Anthropic Claude Documentation](https://docs.anthropic.com/)
- [Aider Documentation](https://aider.chat/docs/)
- [Cline GitHub Repository](https://github.com/saoudrizwan/claude-dev)

---

**Last Updated:** 2026-01-02  
**Maintainer:** Copilot (AAS-101)  
**Version:** 1.0

# GitKraken CLI Workflow for AAS

This guide covers using GitKraken CLI to enhance AAS development workflows with automated Git operations, PR management, and issue tracking.

## Overview

GitKraken CLI (`gk`) provides enterprise-grade Git automation that integrates perfectly with AAS's multi-agent architecture:

- **Unified Git+Issues**: Single tool for Git operations and Linear/GitHub Issues
- **Cloud Patches**: Share WIP without pushing branches
- **Workspace Sync**: Auto-sync with GitKraken Desktop
- **PR Automation**: Auto-create PRs when tasks completed
- **Team Visibility**: GitKraken Insights for agent activity

## Installation

### Option 1: NPM (Recommended)
```bash
npm install -g @gitkraken/cli
```

### Option 2: Clone from Source
```bash
git clone https://github.com/gitkraken/gk-cli.git
cd gk-cli
npm install
npm link
```

### Verify Installation
```bash
gk --version
```

## Authentication

First-time setup:
```bash
# Login to GitKraken
gk auth login

# Connect to Linear (if using Linear integration)
gk provider connect linear

# Connect to GitHub (if using GitHub Issues)
gk provider connect github
```

## AAS Integration Points

### 1. HandoffManager Integration

The `core/handoff/gitkraken.py` module provides seamless integration:

```python
from core.handoff_gitkraken import get_gitkraken_workflow

# Initialize workflow
gk_workflow = get_gitkraken_workflow()

if gk_workflow:
    # Start a task (creates branch)
    gk_workflow.start_task("AAS-027", "GitKraken CLI Integration")
    
    # Complete a task (creates PR)
    pr_url = gk_workflow.complete_task(
        "AAS-027",
        "GitKraken CLI Integration",
        "Implemented full gk integration with HandoffManager"
    )
    
    # Snapshot progress (creates cloud patch)
    patch_id = gk_workflow.snapshot_progress(
        "AAS-027",
        "50% complete - core integration done, docs in progress"
    )
```

### 2. Background Agent Workflows

Cloud patches are perfect for background agents (Aider, Claude Code):

```bash
# Agent starts work
git worktree add ../AAS-agent-1 -b task/AAS-016
cd ../AAS-agent-1

# Agent makes progress
# ... code changes ...

# Agent creates snapshot
gk patch create --name "AAS-016-agent-wip" --description "IPC refactor 60% complete"

# Human reviews without merging
gk patch view AAS-016-agent-wip
gk patch apply AAS-016-agent-wip  # In a review worktree
```

### 3. Linear Integration Enhancement

Replace raw Linear API calls with gk:

```python
from core.handoff_gitkraken import GitKrakenCLI

gk = GitKrakenCLI()

# List open Linear issues
issues = gk.list_issues(state="open", labels=["aas", "urgent"])

# Sync with Linear
for issue in issues:
    # Auto-create task in ACTIVE_TASKS.md
    # Create branch for immediate claiming
    gk.create_branch(f"task/{issue['id']}")
```

### 4. PR Automation

Automated PR creation when tasks marked Done:

```python
# In HandoffManager.mark_task_done()
from core.handoff_gitkraken import get_gitkraken_workflow

gk_workflow = get_gitkraken_workflow()
if gk_workflow:
    # Auto-create PR with task details
    pr_url = gk_workflow.complete_task(
        task_id=task['id'],
        task_title=task['title'],
        completion_notes=f"Completed by {task['assignee']}"
    )
    
    # Update task with PR link
    task['pr_url'] = pr_url
```

## Common Workflows

### Workflow 1: Start New Task
```bash
# Claim task from board
python core/main.py claim AAS-027

# Auto-create branch via gk
gk branch create task/AAS-027-gitkraken-cli --base master

# Start work
# ... code changes ...
```

### Workflow 2: Snapshot Progress
```bash
# End of day or before context switch
gk patch create --name "AAS-027-eod-jan2" --description "Core integration complete, docs 70%"

# Continue later
gk patch list
gk patch apply AAS-027-eod-jan2
```

### Workflow 3: Complete Task with PR
```bash
# Finish work
git add .
git commit -m "feat(AAS-027): implement GitKraken CLI integration"

# Create PR via gk
gk pr create \
  --title "feat(AAS-027): GitKraken CLI Integration" \
  --body "Implements full gk integration for automated workflows" \
  --base master

# Mark task done in AAS
python core/main.py done AAS-027
```

### Workflow 4: Review Agent Work
```bash
# List patches created by agents
gk patch list --author "aider-agent"

# Review in isolated worktree
git worktree add ../review-space -b review/temp
cd ../review-space
gk patch apply AAS-016-agent-wip

# Review changes
git diff master

# Approve or request changes
gk pr review --approve  # or --request-changes
```

## GitKraken Workspace Setup

### Create Cloud Workspace
```bash
# Initialize workspace
gk workspace create --name "AaroneousAutomationSuite"

# Add team members
gk workspace invite user@example.com

# Sync repository
gk workspace sync
```

### Benefits of Cloud Workspace
- **Team Visibility**: See who's working on what in real-time
- **Activity Feed**: Track all Git operations across team
- **Insights**: Metrics on commit frequency, PR velocity, etc.
- **Cloud Patches**: Share WIP without polluting branch history

## Configuration

### .gk/config.yml (Project-level)
```yaml
# GitKraken CLI Configuration for AAS
workspace:
  name: AaroneousAutomationSuite
  auto_sync: true

branches:
  prefix: task/
  naming: "{task_id}-{title}"
  base: master

pull_requests:
  auto_create: true
  draft_by_default: false
  template: |
    ## Task: {task_id}
    
    **Title:** {task_title}
    
    ### Completion Notes
    {completion_notes}
    
    Closes {task_id}

patches:
  auto_snapshot: true
  snapshot_interval: 3600  # hourly for long-running agents

integrations:
  linear:
    enabled: true
    auto_sync: true
  github:
    enabled: true
```

### Integration with HandoffManager

Add to `core/handoff/manager.py`:

```python
from core.handoff_gitkraken import get_gitkraken_workflow

class HandoffManager:
    def __init__(self, config, artifact_dir):
        # ... existing init ...
        
        # Initialize GitKraken workflow
        self.gk_workflow = get_gitkraken_workflow()
        if self.gk_workflow:
            logger.info("GitKraken workflow automation enabled")
    
    def claim_task(self, task_id: str, assignee: str) -> bool:
        # ... existing claim logic ...
        
        # Auto-create branch
        if self.gk_workflow:
            task = self.get_task(task_id)
            self.gk_workflow.start_task(task_id, task['title'])
        
        return True
    
    def mark_task_done(self, task_id: str, completion_notes: str) -> bool:
        # ... existing completion logic ...
        
        # Auto-create PR
        if self.gk_workflow:
            task = self.get_task(task_id)
            pr_url = self.gk_workflow.complete_task(
                task_id,
                task['title'],
                completion_notes
            )
            
            if pr_url:
                logger.info(f"PR created for {task_id}: {pr_url}")
        
        return True
```

## Advanced Features

### 1. Issue Sync from Linear
```bash
# Pull Linear issues into local board
gk issue list --state open --provider linear --json > /tmp/issues.json

# Python script to sync
import json
from core.handoff_manager import HandoffManager

with open('/tmp/issues.json') as f:
    issues = json.load(f)

manager = HandoffManager()
for issue in issues:
    manager.add_task_from_linear(issue)
```

### 2. Automated Agent Checkpoints
```bash
# In background agent script
while task_not_complete:
    # Do work
    make_code_changes()
    
    # Checkpoint every hour
    if time_since_last_checkpoint > 3600:
        gk patch create --name "AAS-016-auto-checkpoint-$(date +%s)"
```

### 3. PR Status Monitoring
```python
from core.handoff_gitkraken import GitKrakenCLI

gk = GitKrakenCLI()

# Monitor PR for task
pr_status = gk.get_pr_status(pr_number=42)

if pr_status['state'] == 'merged':
    # Task fully complete
    manager.archive_task(task_id)
```

## Troubleshooting

### gk command not found
```bash
# Check PATH
echo $PATH

# Re-link if installed via npm
npm link @gitkraken/cli

# Or add to PATH
export PATH="$PATH:$(npm root -g)/.bin"
```

### Authentication issues
```bash
# Re-authenticate
gk auth logout
gk auth login

# Check token
gk auth status
```

### Cloud patch not syncing
```bash
# Force sync
gk workspace sync --force

# Check connection
gk config get workspace.url
```

## Best Practices

1. **Always use branches**: Never work directly on master
2. **Snapshot frequently**: Cloud patches are cheap, use them liberally
3. **Descriptive names**: Use task IDs in branch/patch names
4. **PR early**: Create draft PRs to signal WIP
5. **Review patches**: Don't merge agent work without human review

## Cost & Licensing

GitKraken CLI is **free for public repositories** and personal use. For private repos and teams, see [GitKraken pricing](https://www.gitkraken.com/pricing).

AAS (MIT License) + GitKraken = Powerful combo for OSS projects.

## Next Steps

1. **Install gk CLI**: `npm install -g @gitkraken/cli`
2. **Authenticate**: `gk auth login`
3. **Test integration**: `python -c "from core.handoff_gitkraken import get_gitkraken_workflow; print(get_gitkraken_workflow())"`
4. **Update HandoffManager**: Add gk workflow calls
5. **Configure agents**: Use cloud patches for background work

## References

- GitKraken CLI Docs: https://help.gitkraken.com/gk-cli/
- GitHub Repo: https://github.com/gitkraken/gk-cli
- Linear Integration: https://help.gitkraken.com/gk-cli/integrations/#linear
- Cloud Patches: https://help.gitkraken.com/gk-cli/cloud-patches/

# Linear Integration Guide

> Complete guide to integrating AAS with your Linear workspace

This guide walks through integrating the Aaroneous Automation Suite (AAS) with Linear for seamless task management, issue tracking, and AI agent coordination.

## Prerequisites

- Admin access to Linear workspace
- GitHub repository access (Aarogaming/AaroneousAutomationSuite)
- `.env` file configured with Linear credentials

## Quick Start

### Linear Team
- **Team**: Aaroneous Automation Suite  
- **Workspace**: https://linear.app/aarogaming
- **Team ID**: Configure in `.env` as `LINEAR_TEAM_ID`

## Integration Steps

### 1. Install Linear GitHub App

1. Visit https://linear.app/aarogaming/settings/integrations
2. Find "GitHub" integration and click "Add"
3. Authorize Linear to access your GitHub organization
4. Select `Aarogaming/AaroneousAutomationSuite` repository
5. Configure permissions:
   - ✅ Read issues and pull requests
   - ✅ Write comments
   - ✅ Update issue status

### 2. Configure Linear API Access

Add to your `.env` file:
```env
LINEAR_API_KEY=lin_api_your-key-here
LINEAR_TEAM_ID=your-team-id
```

Get your API key: https://linear.app/aarogaming/settings/api

### 3. Enable Bidirectional Sync

In Linear Settings → Integrations → GitHub:
- ✅ Enable "Create Linear issues from GitHub issues"
- ✅ Enable "Sync status changes"
- ✅ Enable "Sync comments"
- ✅ Enable "Auto-close on merge"

### 4. Verify Integration

Run the automated verification tool:
```bash
python scripts/verify_linear.py
```

This will:
- ✅ Test API key validity
- ✅ List available teams
- ✅ Create and archive a test issue
- ✅ Verify LinearSync class functionality

Expected output:
```
============================================================
LINEAR INTEGRATION VERIFICATION
============================================================

🔑 Verifying Linear API key...
   ✅ API key valid
   👤 User: Your Name (your@email.com)

📋 Fetching teams...
   ✅ Found 1 team(s):
      • Aaroneous Automation Suite (ID: xxx, Key: AAS)

✅ Using configured team: Aaroneous Automation Suite

🧪 Testing issue creation...
   ✅ Created test issue: AAS-XXX
   ✅ Archived test issue (cleanup)

✅ Linear integration is working correctly!
```

## Automatic Syncing

### GitHub → Linear
- **GitHub Issues** automatically create Linear issues
- **PR references** (e.g., "Fixes AAS-018") link to Linear tasks
- **Commit messages** with Linear IDs (e.g., "AAS-018: Fix adapter") auto-link

### Linear → GitHub
- **Linear issues** can optionally create GitHub issues
- **Status changes** sync between platforms
- **Comments** sync bidirectionally

## Using Linear IDs in Git

### Commit Messages
```bash
git commit -m "AAS-018: Implement universal game adapter interface"
```

### Branch Names
```bash
git checkout -b feature/AAS-018-adapter-interface
```

### Pull Requests
```markdown
## Description
Implements AAS-018: Universal Game Adapter Interface

## Linear Issue
Fixes AAS-018
```

## GitHub Copilot Integration

GitHub Copilot can now:
- Reference Linear issues in code suggestions
- Understand project context from Linear descriptions
- Generate code aligned with Linear task requirements

To help Copilot understand Linear context, use this in your PR descriptions or comments:
```
Linear Issue: AAS-XXX
Context: [Brief description from Linear]
```

## Automation Rules

### Auto-Close Linear Issues
When a PR is merged that references a Linear issue:
1. PR merge triggers Linear status update
2. Linear issue transitions to "Done"
3. Completion date is recorded

### Branch Creation
Use Linear's "Create branch" feature:
1. Open Linear issue (e.g., AAS-025)
2. Click "Create branch" in Linear
3. Linear creates GitHub branch with proper naming
4. Branch auto-links to Linear issue

## API Integration

The AAS Hub includes Linear API integration (`core/handoff/linear.py`):
- Automatic task sync from `ACTIVE_TASKS.md` to Linear
- Error reporting creates Linear issues
- Health reports post to Linear

Configure via `.env`:
```env
LINEAR_API_KEY=your-key-here
LINEAR_TEAM_ID=your-team-id
```

## Troubleshooting

### Integration Not Connecting
- **Check Admin Rights**: Ensure you have admin access on both Linear and GitHub
- **Review Audit Logs**: Linear Settings → Audit Log for permission issues
- **Verify Repository Access**: Confirm repository is in authorized list

### Sync Delays
- **Normal Delay**: Up to 1 minute for sync to process
- **Webhook Issues**: Check Linear Settings → Integrations → GitHub → Webhook logs
- **Rate Limiting**: Linear API has rate limits; check response headers

### IDs Not Linking
- **Format**: Must be `AAS-XXX` (team prefix + number)
- **Placement**: Use in commit messages, PR titles, or PR body
- **Team Prefix**: Verify your team's prefix in Linear Settings

### API Authentication Errors
```bash
# Test API key validity
curl -H "Authorization: YOUR_LINEAR_API_KEY" https://api.linear.app/graphql \
  -d '{"query":"{ viewer { id name } }"}'
```

If you see authentication errors:
1. Regenerate API key in Linear Settings → API
2. Update `.env` file
3. Restart AAS Hub: `python core/main.py`

## Best Practices

### Security
- 🔒 **Never commit** Linear API keys to Git (use `.env` and `.gitignore`)
- 🔄 **Rotate keys** periodically (every 90 days recommended)
- 👥 **Team-level access**: Use Linear team settings for granular permissions
- 📝 **Audit regularly**: Review Linear audit logs for unexpected access

### Task Management
- 📋 **Use Linear as source of truth** for task status
- 🔗 **Always reference Linear IDs** in commits and PRs
- ✅ **Update via PRs**: Let PR merges auto-close Linear issues
- 📊 **Track in ACTIVE_TASKS.md**: Local board syncs with Linear

### Workflow Integration
- 🌿 **Branch from Linear**: Use "Create branch" feature for auto-linking
- 💬 **Comment in Linear**: AI agents post updates to Linear issues
- 🚨 **Error reporting**: Critical errors auto-create Linear issues
- 📈 **Health reports**: System health syncs to Linear

## Advanced Features

### AI Agent Integration

AAS AI agents (Copilot, Sixth, CodeGPT) automatically:
- Pull tasks from Linear via `get_active_tasks()`
- Post completion reports to Linear
- Create issues for errors via `HandoffManager.report_event()`
- Sync `ACTIVE_TASKS.md` status to Linear

### Session Context

When creating a new Copilot session, reference Linear context:
```markdown
## Context from Linear (AAS-XXX)
**Title**: [Task title]
**Description**: [Task description]
**Dependencies**: [AAS-001, AAS-002]
```

This helps Copilot understand project context and make aligned suggestions.

### Webhook Events

Linear webhook events trigger AAS actions:
- `Issue.create` → Add to ACTIVE_TASKS.md
- `Issue.update` → Sync status changes
- `Issue.complete` → Run completion hooks
- `Comment.create` → Notify assigned agents

Configure webhooks: Linear Settings → Integrations → Webhooks

## Verification Checklist

After setup, verify these work:

- [ ] Create test Linear issue → Appears in GitHub
- [ ] Commit with `AAS-XXX` → Links to Linear issue  
- [ ] Merge PR with "Fixes AAS-XXX" → Linear issue auto-closes
- [ ] Comment in Linear → Syncs to GitHub
- [ ] Run `python scripts/test_gitkraken.py` → Linear operations pass
- [ ] Check `artifacts/handoff/reports/HEALTH_REPORT.md` → Linear status shown

## Troubleshooting

### Sync Not Working
1. Check GitHub App permissions in Linear
2. Verify repository is authorized
3. Check Linear workspace settings

### IDs Not Linking
- Ensure format is `AAS-XXX` (team prefix + number)
- Use Linear IDs in commit messages, PR titles, or PR body
- Wait up to 1 minute for sync to process

## Security and Compliance

### Data Protection
- **Encryption**: All API calls use HTTPS/TLS
- **Secret Management**: API keys stored as `SecretStr` in Pydantic models
- **No Plain Text**: Secrets never logged or displayed in plain text
- **Environment Variables**: Keys loaded from `.env` (gitignored)

### Audit Trail
Linear maintains complete audit logs:
- Who accessed what resources
- When changes were made
- API key usage patterns

Access audit logs: Linear Settings → Security → Audit Log

### Compliance
- **GDPR**: Linear is GDPR compliant
- **SOC 2**: Linear maintains SOC 2 Type II certification
- **Data Residency**: Data stored in US/EU (configurable)

For security concerns, contact Linear support or review:
- [Linear Security Documentation](https://linear.app/docs/security)
- [Linear Privacy Policy](https://linear.app/privacy)

## Related Documentation
- [Linear API Integration](../core/handoff/README.md)
- [Handoff Protocol](../handoff/ACTIVE_TASKS.md)
- [GitHub Copilot Instructions](../.github/copilot-instructions.md)

# Security Guidelines - Aaroneous Automation Suite

## Overview
This document outlines security practices and guidelines for the AAS project to ensure sensitive data protection and secure development practices.

## Critical Security Rules

### 1. **NEVER Commit Secrets**
- ❌ **NEVER** commit `.env` files
- ❌ **NEVER** commit API keys, tokens, or passwords
- ❌ **NEVER** commit private keys or certificates
- ✅ **ALWAYS** use `.env.example` as a template
- ✅ **ALWAYS** use environment variables for secrets
- ✅ **ALWAYS** use `SecretStr` in Pydantic models

### 2. **Environment Variable Management**

#### Correct Usage
```python
from pydantic import SecretStr, Field

class Config(BaseSettings):
    openai_api_key: SecretStr = Field(..., alias="OPENAI_API_KEY")
    
# Access secret value only when needed
api_key = config.openai_api_key.get_secret_value()
```

#### What NOT to Do
```python
# ❌ Don't hardcode secrets
API_KEY = "sk-proj-abc123..."

# ❌ Don't log secrets
logger.info(f"API Key: {api_key}")

# ❌ Don't expose in error messages
raise Exception(f"Failed with key {api_key}")
```

### 3. **Git Security Best Practices**

#### Before Each Commit
```bash
# 1. Check for secrets in staged files
git diff --cached | grep -iE "(api[_-]?key|secret|token|password)"

# 2. Run the secrets scanner
pwsh game_manager/maelstrom/scripts/scan_for_secrets.ps1

# 3. Verify .env is not staged
git status | grep ".env"
```

#### If You Accidentally Commit Secrets
1. **Immediately rotate the compromised credentials**
2. Remove from git history:
```bash
# Remove file from all commits
git filter-branch --force --index-filter \
  "git rm --cached --ignore-unmatch .env" \
  --prune-empty --tag-name-filter cat -- --all

# Force push (coordinate with team first!)
git push origin --force --all
```

### 4. **Protected Files & Patterns**

The `.gitignore` file excludes these sensitive patterns:

#### Environment Files
- `.env`, `.env.local`, `.env.*.local`
- `*.env` (any environment file)

#### Credentials & Keys
- `*.key`, `*.pem`, `*.pfx`, `*.p12`
- `*.jks`, `*.keystore`
- `credentials.json`, `service-account*.json`
- `id_rsa*`, `id_dsa*`, `id_ecdsa*`, `id_ed25519*`

#### Certificates
- `*.cert`, `*.cer`, `*.crt`
- `*.certSigningRequest`
- `private.key`, `privatekey.pem`

### 5. **API Key Security**

#### OpenAI API Keys
- **Format:** `sk-proj-...` (48+ characters)
- **Storage:** `.env` file only
- **Rotation:** Every 90 days or on suspected compromise
- **Scope:** Use project-specific keys, not personal keys

#### Linear API Keys
- **Format:** `lin_api_...` (40+ characters)
- **Storage:** `.env` file only
- **Permissions:** Minimum required (read/write issues only)

#### GitHub Tokens
- **Format:** `ghp_...` or `gho_...` (36+ characters)
- **Storage:** `.env` or secure credential manager
- **Scope:** Limit to specific repositories and permissions

### 6. **Configuration Security Pattern**

AAS uses the Resilient Configuration System (RCS) for secure config management:

```python
# core/config/manager.py
from pydantic import BaseSettings, SecretStr, Field

class AASConfig(BaseSettings):
    # Secrets are wrapped in SecretStr
    openai_api_key: SecretStr = Field(
        ..., 
        alias="OPENAI_API_KEY",
        description="OpenAI API key for GPT models"
    )
    
    # Public config can use regular types
    debug_mode: bool = Field(
        default=False,
        alias="DEBUG_MODE"
    )
    
    class Config:
        env_file = ".env"
        env_file_encoding = "utf-8"
        case_sensitive = False
```

### 7. **Logging Security**

#### DO:
```python
from loguru import logger

# Safe logging
logger.info("API request successful")
logger.debug(f"Request to endpoint: {endpoint}")

# Mask sensitive data
masked_key = f"{api_key[:8]}...{api_key[-4:]}"
logger.info(f"Using API key: {masked_key}")
```

#### DON'T:
```python
# ❌ Never log full secrets
logger.info(f"API Key: {api_key}")

# ❌ Never log credentials in exceptions
logger.error(f"Auth failed with token {token}")
```

### 8. **IPC Security (gRPC)**

Current state: **Insecure** (localhost only)

#### Current Risk
- No encryption (plaintext communication)
- No authentication
- Limited to localhost (127.0.0.1)

#### Planned Improvements (see ROADMAP.md)
- [ ] Implement mTLS (mutual TLS)
- [ ] Add API key authentication
- [ ] Rate limiting
- [ ] Request/response signing

#### Current Mitigation
- Only bind to `localhost:50051`
- Firewall blocks external connections
- Run behind VPN for remote access

### 9. **Dependency Security**

#### Regular Security Audits
```bash
# Python dependencies
pip install safety
safety check

# Check for outdated packages
pip list --outdated
```

#### Update Strategy
- Review `requirements.txt` monthly
- Update critical security patches immediately
- Test updates in development before production
- Pin versions for reproducibility

### 10. **Plugin Security**

Plugins have access to the Hub's config. Security considerations:

#### Plugin Development
- **Validate all inputs** before processing
- **Sanitize file paths** to prevent traversal attacks
- **Limit file system access** to plugin directory
- **Never log secrets** from Hub config
- **Use Hub's error reporting** (don't expose internals)

#### Plugin Review Checklist
- [ ] No hardcoded credentials
- [ ] Proper input validation
- [ ] No arbitrary code execution
- [ ] Limited file system access
- [ ] Secure error handling

### 11. **Incident Response**

If you discover a security issue:

1. **DO NOT** disclose publicly
2. **DO** rotate compromised credentials immediately
3. **DO** notify the team via secure channel
4. **DO** document the incident (without sensitive details)
5. **DO** update this guide with lessons learned

#### Reporting Security Issues
- **Internal:** Slack #security channel (if exists)
- **External:** Create a private GitHub issue or email maintainer
- **Critical:** Immediate notification required

### 12. **Pre-Commit Security Checklist**

Before every commit, verify:

- [ ] No `.env` files in staged changes
- [ ] No API keys in code (use `git diff --cached | grep -iE "sk-|ghp_|lin_api_"`)
- [ ] No passwords in comments or docs
- [ ] No database credentials
- [ ] No private keys or certificates
- [ ] All secrets use `SecretStr` or environment variables
- [ ] No debug logs exposing sensitive data

### 13. **Automation & CI/CD Security**

#### GitHub Actions / CI Secrets
- Store in GitHub Secrets, not in workflow files
- Use `${{ secrets.SECRET_NAME }}` syntax
- Never echo secrets in logs
- Limit secret access to necessary workflows

#### Example Secure Workflow
```yaml
name: Deploy
on: [push]
jobs:
  deploy:
    runs-on: ubuntu-latest
    steps:
      - name: Deploy
        env:
          API_KEY: ${{ secrets.OPENAI_API_KEY }}
        run: |
          # ✅ Secret available as env var, not logged
          python deploy.py
```

### 14. **Local Development Security**

#### Workstation Security
- Use full disk encryption
- Enable Windows BitLocker or macOS FileVault
- Use strong passwords/passphrases
- Lock workstation when away (Win+L)
- Keep OS and software updated

#### .env File Permissions
```bash
# Restrict .env to owner read/write only
chmod 600 .env  # Linux/macOS

# Windows: Right-click .env → Properties → Security → Advanced
# Remove all users except yourself
```

### 15. **Code Review Security**

When reviewing PRs, check for:

- [ ] No new secrets in code
- [ ] Proper use of `SecretStr`
- [ ] No sensitive data in test files
- [ ] Secure error handling (no credential leaks)
- [ ] Updated `.env.example` if new config added
- [ ] No exposed internal paths or IPs

### 16. **Third-Party Integration Security**

#### Project Maelstrom (C#)
- Shares IPC channel (localhost gRPC)
- Can send commands to AAS Hub
- **Risk:** Malicious commands if Maelstrom compromised
- **Mitigation:** Command validation, rate limiting (planned)

#### Home Assistant
- Uses long-lived access token
- **Risk:** Token has full home control access
- **Mitigation:** Create limited-scope token when possible

#### Linear API
- Can create/modify issues
- **Risk:** Spam, data manipulation
- **Mitigation:** Rate limiting, webhook verification (planned)

### 17. **Future Security Roadmap**

See [ROADMAP.md](ROADMAP.md) for:
- mTLS for IPC bridge
- OAuth2 for third-party integrations
- Secrets management via HashiCorp Vault
- Audit logging system
- Role-based access control (RBAC)

## Quick Reference: Common Scenarios

### "I need to add a new API key"
1. Add to `.env.example` as placeholder
2. Add `SecretStr` field to `core/config/manager.py`
3. Document in `.env.example` comments
4. Never commit actual key value

### "I accidentally committed a secret"
1. **Immediately** rotate the secret
2. Remove from git history (see section 3)
3. Verify it's in `.gitignore`
4. Report to team

### "I want to test with real API keys"
1. Create `.env` from `.env.example`
2. Add real values to `.env`
3. Verify `.env` is in `.gitignore`
4. Never commit or share `.env`

### "Plugin needs access to config"
```python
# In plugin register() function
def register(hub: Hub):
    # Access config via hub
    if hub.config.openai_api_key:
        api_key = hub.config.openai_api_key.get_secret_value()
        # Use api_key
    else:
        logger.warning("OpenAI API key not configured")
```

## Additional Resources

- [OWASP Top 10](https://owasp.org/www-project-top-ten/)
- [GitHub Secret Scanning](https://docs.github.com/en/code-security/secret-scanning)
- [Pydantic SecretStr Documentation](https://docs.pydantic.dev/latest/api/types/#pydantic.types.SecretStr)
- [Python Security Best Practices](https://python.readthedocs.io/en/stable/library/security_warnings.html)

---

**Last Updated:** January 5, 2026  
**Maintained by:** AAS Development Team  
**Status:** Living document - Update as security practices evolve

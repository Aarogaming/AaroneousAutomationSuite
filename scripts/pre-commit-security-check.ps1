#!/usr/bin/env pwsh
# ==============================================================================
# Pre-Commit Security Check for AAS
# ==============================================================================
# This script runs before each commit to detect potential security issues
# Place in .git/hooks/pre-commit and make executable

param(
    [switch]$BypassSecurityCheck = $false
)

Set-StrictMode -Version Latest
$ErrorActionPreference = "Stop"

Write-Host "🔒 Running pre-commit security checks..." -ForegroundColor Cyan

$issues = @()

# ==============================================================================
# 1. Check for .env files
# ==============================================================================
Write-Host "  ✓ Checking for .env files..." -NoNewline
$envFiles = git diff --cached --name-only | Select-String -Pattern "\.env$"
if ($envFiles) {
    $issues += "❌ .env file detected in commit: $envFiles"
    Write-Host " FAILED" -ForegroundColor Red
} else {
    Write-Host " OK" -ForegroundColor Green
}

# ==============================================================================
# 2. Check for common API key patterns
# ==============================================================================
Write-Host "  ✓ Scanning for API keys..." -NoNewline
$patterns = @(
    "sk-proj-[a-zA-Z0-9]{20,}",     # OpenAI
    "ghp_[a-zA-Z0-9]{36}",           # GitHub Personal Access Token
    "gho_[a-zA-Z0-9]{36}",           # GitHub OAuth Token
    "lin_api_[a-zA-Z0-9]{40}",       # Linear API
    "xoxb-[a-zA-Z0-9-]+",            # Slack Bot Token
    "AIza[0-9A-Za-z\-_]{35}"         # Google API Key
)

$found = $false
foreach ($pattern in $patterns) {
    $matches = git diff --cached | Select-String -Pattern $pattern
    if ($matches) {
        $issues += "❌ Potential API key pattern detected: $pattern"
        $found = $true
    }
}

if ($found) {
    Write-Host " FAILED" -ForegroundColor Red
} else {
    Write-Host " OK" -ForegroundColor Green
}

# ==============================================================================
# 3. Check for private keys
# ==============================================================================
Write-Host "  ✓ Checking for private keys..." -NoNewline
$keyPatterns = @(
    "BEGIN PRIVATE KEY",
    "BEGIN RSA PRIVATE KEY",
    "BEGIN DSA PRIVATE KEY",
    "BEGIN EC PRIVATE KEY",
    "BEGIN OPENSSH PRIVATE KEY"
)

$foundKeys = $false
foreach ($keyPattern in $keyPatterns) {
    $matches = git diff --cached | Select-String -Pattern $keyPattern
    if ($matches) {
        # Exclude matches in security scanning tools
        $excluded = $matches | Where-Object { 
            $_.Path -notmatch "(scan_for_secrets|ApiSender|HandoffUtility)" 
        }
        if ($excluded) {
            $issues += "❌ Private key detected in: $($excluded.Path)"
            $foundKeys = $true
        }
    }
}

if ($foundKeys) {
    Write-Host " FAILED" -ForegroundColor Red
} else {
    Write-Host " OK" -ForegroundColor Green
}

# ==============================================================================
# 4. Check for common credential keywords in actual values
# ==============================================================================
Write-Host "  ✓ Checking for credential keywords..." -NoNewline
$credPatterns = @(
    'password\s*[=:]\s*["\'][^"\']{3,}["\']',
    'token\s*[=:]\s*["\'][^"\']{10,}["\']',
    'secret\s*[=:]\s*["\'][^"\']{10,}["\']'
)

$foundCreds = $false
foreach ($credPattern in $credPatterns) {
    $matches = git diff --cached | Select-String -Pattern $credPattern
    if ($matches) {
        # Exclude test files and examples
        $excluded = $matches | Where-Object { 
            $_.Path -notmatch "(test_|_test\.py|\.example|\.md|conftest\.py)" 
        }
        if ($excluded) {
            $issues += "⚠️  Potential credential detected: $($excluded.Path):$($excluded.LineNumber)"
            $foundCreds = $true
        }
    }
}

if ($foundCreds) {
    Write-Host " WARNING" -ForegroundColor Yellow
} else {
    Write-Host " OK" -ForegroundColor Green
}

# ==============================================================================
# 5. Check for large files (potential sensitive data)
# ==============================================================================
Write-Host "  ✓ Checking for large files..." -NoNewline
$largeFiles = git diff --cached --name-only | ForEach-Object {
    if (Test-Path $_) {
        $size = (Get-Item $_).Length
        if ($size -gt 5MB) {
            [PSCustomObject]@{
                Path = $_
                Size = [math]::Round($size / 1MB, 2)
            }
        }
    }
}

if ($largeFiles) {
    foreach ($file in $largeFiles) {
        $issues += "⚠️  Large file detected: $($file.Path) ($($file.Size) MB)"
    }
    Write-Host " WARNING" -ForegroundColor Yellow
} else {
    Write-Host " OK" -ForegroundColor Green
}

# ==============================================================================
# Report Results
# ==============================================================================
Write-Host ""
if ($issues.Count -eq 0) {
    Write-Host "✅ All security checks passed!" -ForegroundColor Green
    Write-Host ""
    exit 0
} else {
    Write-Host "❌ Security issues detected:" -ForegroundColor Red
    Write-Host ""
    
    foreach ($issue in $issues) {
        Write-Host "  $issue"
    }
    
    Write-Host ""
    Write-Host "Please fix these issues before committing." -ForegroundColor Yellow
    Write-Host ""
    Write-Host "If you're certain this is a false positive, you can bypass with:" -ForegroundColor Cyan
    Write-Host "  git commit --no-verify" -ForegroundColor Gray
    Write-Host ""
    Write-Host "⚠️  REMEMBER: Never commit actual secrets! Use .env files." -ForegroundColor Yellow
    Write-Host ""
    
    if ($BypassSecurityCheck) {
        Write-Host "⚠️  Security check bypassed by user." -ForegroundColor Yellow
        exit 0
    }
    
    exit 1
}

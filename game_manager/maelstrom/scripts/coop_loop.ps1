param(
    [string]$InputPath = "artifacts/codex_output.txt",
    [switch]$Watch
)

Set-StrictMode -Version Latest
$ErrorActionPreference = "Stop"

# Ensure artifacts directory
$artifactsDir = Split-Path -Parent $InputPath
if ([string]::IsNullOrWhiteSpace($artifactsDir)) { $artifactsDir = "." }
if (-not (Test-Path $artifactsDir)) {
    New-Item -ItemType Directory -Path $artifactsDir | Out-Null
}

Write-Host "=== Co-op Loop ===" -ForegroundColor Cyan
Write-Host "1) Paste Codex output into: $InputPath and save." -ForegroundColor Yellow

$lastWrite = $null
if (Test-Path $InputPath) {
    $lastWrite = (Get-Item $InputPath).LastWriteTimeUtc
}

if ($Watch) {
    Write-Host "Waiting for file change..." -ForegroundColor Gray
    while ($true) {
        Start-Sleep -Seconds 1
        if (-not (Test-Path $InputPath)) { continue }
        $current = (Get-Item $InputPath).LastWriteTimeUtc
        if ($lastWrite -eq $null -or $current -gt $lastWrite) {
            break
        }
    }
} else {
    Read-Host "Press Enter when ready"
}

Write-Host "2) Generating handoff..." -ForegroundColor Cyan
& "$PSScriptRoot/handoff_from_codex.ps1" $InputPath
$exitCode = $LASTEXITCODE
if ($exitCode -ne 0) {
    Write-Host "handoff_from_codex failed (exit $exitCode)" -ForegroundColor Red
    exit $exitCode
}

$handoffPath = Resolve-Path -LiteralPath "HANDOFF.md"
Write-Host "HANDOFF.md copied to clipboard. Paste into ChatGPT now." -ForegroundColor Green
Write-Host "HANDOFF path: $handoffPath"

try {
    Invoke-Item (Split-Path -Parent $handoffPath)
} catch { }

Write-Host "Next: When you get a new Codex prompt, run ./scripts/handoff_to_codex.ps1 and append the footer after your prompt." -ForegroundColor Yellow

exit 0

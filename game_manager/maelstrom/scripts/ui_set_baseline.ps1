param(
    [string]$ConfigPath = "DevTools/UiAuditSelfCapture/ui_self_capture_config.json"
)

Set-StrictMode -Version Latest
$ErrorActionPreference = "Stop"

$repoRoot = Split-Path -Parent $MyInvocation.MyCommand.Path | Split-Path -Parent
$tessdata = Join-Path $repoRoot "tessdata"
if (Test-Path $tessdata) {
    $env:TESSDATA_PREFIX = $tessdata
}

$baselineDir = "ui_baseline"

Write-Host "== UI baseline refresh =="
if (Test-Path $baselineDir) {
    Write-Host "Cleaning $baselineDir ..."
    Remove-Item $baselineDir -Recurse -Force
}
New-Item -ItemType Directory -Path $baselineDir | Out-Null

Write-Host "Running UiAuditSelfCapture to $baselineDir ..."
dotnet run --project DevTools/UiAuditSelfCapture/UiAuditSelfCapture.csproj -- $ConfigPath --out $baselineDir

Write-Host "Baseline ready at: $(Resolve-Path $baselineDir)"

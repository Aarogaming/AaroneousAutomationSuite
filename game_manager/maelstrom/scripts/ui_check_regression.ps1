param(
    [string]$ConfigPath = "DevTools/UiAuditSelfCapture/ui_self_capture_config.json",
    [double]$Threshold = 0.5,
    [string]$ReportPath = "artifacts/ui_diff_report.txt"
)

Set-StrictMode -Version Latest
$ErrorActionPreference = "Stop"

$repoRoot = Split-Path -Parent $MyInvocation.MyCommand.Path | Split-Path -Parent
$tessdata = Join-Path $repoRoot "tessdata"
if (Test-Path $tessdata) {
    $env:TESSDATA_PREFIX = $tessdata
}

$baselineDir = "ui_baseline"
$currentDir = "ui_current"

if (-not (Test-Path $baselineDir)) {
    Write-Error "Baseline not found at '$baselineDir'. Run scripts/ui_set_baseline.ps1 first."
    exit 1
}

Write-Host "== UI regression check =="
if (Test-Path $currentDir) {
    Write-Host "Cleaning $currentDir ..."
    Remove-Item $currentDir -Recurse -Force
}
New-Item -ItemType Directory -Path $currentDir | Out-Null

Write-Host "Capturing current UI to $currentDir ..."
dotnet run --project DevTools/UiAuditSelfCapture/UiAuditSelfCapture.csproj -- $ConfigPath --out $currentDir

$reportDir = Split-Path $ReportPath -Parent
if ([string]::IsNullOrWhiteSpace($reportDir)) {
    $reportDir = "."
}
if (-not (Test-Path $reportDir)) {
    New-Item -ItemType Directory -Path $reportDir -Force | Out-Null
}
$ReportPath = Join-Path (Resolve-Path $reportDir).ProviderPath (Split-Path $ReportPath -Leaf)

$argsList = @(
    "--baseline", $baselineDir,
    "--current", $currentDir,
    "--threshold", $Threshold.ToString(),
    "--report", $ReportPath
)

Write-Host "Running UiAuditDiff (threshold $Threshold) ..."
dotnet run --project DevTools/UiAuditDiff/UiAuditDiff.csproj -- @argsList
$exitCode = $LASTEXITCODE

if ($exitCode -eq 0) {
    Write-Host "UI regression check PASSED. Report: $ReportPath"
} else {
    Write-Host "UI regression check FAILED (code $exitCode). Report: $ReportPath"
}

exit $exitCode

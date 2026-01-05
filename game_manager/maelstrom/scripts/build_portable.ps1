param(
    [switch]$IncludeSamples
)

Set-StrictMode -Version Latest
$ErrorActionPreference = "Stop"

function Write-Summary {
    param($Included, $Excluded)
    Write-Host "`n=== Portable Build Summary ==="
    Write-Host "Included:"
    $Included | ForEach-Object { Write-Host "  - $_" }
    Write-Host "Excluded:"
    $Excluded | ForEach-Object { Write-Host "  - $_" }
}

$repoRoot = Split-Path -Parent $MyInvocation.MyCommand.Path | Split-Path -Parent
Push-Location $repoRoot

$artifacts = Join-Path $repoRoot "artifacts/portable"
if (Test-Path $artifacts) { Remove-Item -Recurse -Force $artifacts }
New-Item -ItemType Directory -Path $artifacts | Out-Null

Write-Host "Building ProjectMaelstrom (Release)..."
dotnet build ProjectMaelstrom/ProjectMaelstrom.sln -c Release

Write-Host "Publishing ProjectMaelstrom (framework-dependent)..."
$publishDir = Join-Path $artifacts "publish"
dotnet publish ProjectMaelstrom/ProjectMaelstrom/ProjectMaelstrom.csproj -c Release -o $publishDir --no-self-contained

# Copy only runtime essentials
$includeList = @(
    "ProjectMaelstrom.exe",
    "ProjectMaelstrom.dll",
    "ProjectMaelstrom.runtimeconfig.json",
    "execution_policy.conf"
)

Write-Host "Collecting runtime files..."
$files = Get-ChildItem $publishDir
foreach ($item in $files) {
    if ($includeList -contains $item.Name -or $item.Extension -in @(".dll", ".json", ".config")) {
        Copy-Item $item.FullName -Destination $artifacts -Force
    }
}

# Ensure default policy exists (safe defaults)
$policyPath = Join-Path $artifacts "execution_policy.conf"
if (-not (Test-Path $policyPath)) {
    Set-Content $policyPath "ALLOW_LIVE_AUTOMATION=false`nEXECUTION_PROFILE=AcademicSimulation`n"
}

# Plugins folder
$pluginDest = Join-Path $artifacts "plugins"
New-Item -ItemType Directory -Path $pluginDest -Force | Out-Null

if ($IncludeSamples) {
    $samples = Join-Path $repoRoot "plugins/_samples"
    if (Test-Path $samples) {
        Copy-Item -Recurse -Force $samples $pluginDest
    }
}

# Exclusions
$excluded = @(
    "DevTools/**",
    "*TestRunner*",
    "plugins/_samples (unless -IncludeSamples)",
    "publish intermediate"
)

$included = @(
    "Core app binaries (Release, framework-dependent)",
    "execution_policy.conf (safe defaults)",
    "plugins/ (empty by default)"
)
if ($IncludeSamples) { $included += "plugins/_samples (SampleReplayAnalyzer, etc.)" }

Write-Summary -Included $included -Excluded $excluded
Write-Host "`nPortable output: $artifacts"

Pop-Location

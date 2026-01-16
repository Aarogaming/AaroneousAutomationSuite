param(
  [string]$Configuration = "Release"
)

$ErrorActionPreference = 'Stop'

$repoRoot = Split-Path -Parent $PSScriptRoot

Write-Host "Validating contracts in $repoRoot" -ForegroundColor Cyan

$toolProject = Join-Path $repoRoot "Workbench\Tools\MaelstromToolkit\MaelstromToolkit.csproj"
if (!(Test-Path $toolProject)) {
  throw "MaelstromToolkit not found at $toolProject"
}

& dotnet run --project $toolProject -c $Configuration -- contracts validate --root $repoRoot

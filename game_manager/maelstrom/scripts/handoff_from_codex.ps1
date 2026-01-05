param(
    [Parameter(Mandatory=$true)]
    [string]$InputPath
)

Set-StrictMode -Version Latest
$ErrorActionPreference = "Stop"

if (-not (Test-Path $InputPath)) {
Write-Error "Input file not found: $InputPath"
exit 1
}

Write-Host "Running HandoffUtility..." -ForegroundColor Cyan
dotnet run --project DevTools/HandoffUtility/HandoffUtility.csproj -- "$InputPath" --clipboard --zip
$exit = $LASTEXITCODE

if ($exit -eq 0) {
    $handoff = Resolve-Path -LiteralPath "HANDOFF.md"
    $zipPath = "handoff_pack.zip"
    Write-Host "Handoff ready:" -ForegroundColor Green
    Write-Host "  HANDOFF.md     -> $handoff"
    if (Test-Path $zipPath) {
        $zip = Resolve-Path -LiteralPath $zipPath
        Write-Host "  handoff_pack.zip -> $zip"
    }
    Write-Host "Clipboard updated with HANDOFF.md contents."
} else {
    Write-Host "HandoffUtility failed (exit $exit)." -ForegroundColor Red
}

exit $exit

param(
  [Parameter(Mandatory=$true)][string]$Channel,
  [Parameter(Mandatory=$true)][string]$ConsumerId,
  [int]$MaxPerLoop = 1,
  [int]$LoopDelayMs = 1000,
  [switch]$Once,
  [scriptblock]$ProcessScript
)

$ErrorActionPreference = 'Stop'

$repoRoot = Split-Path -Parent $PSScriptRoot
$claimScript = Join-Path $repoRoot 'eng/ipc-claim.ps1'
$base = Join-Path $repoRoot "artifacts/ipc/$Channel"
$archiveBase = Join-Path $base 'archive'
$archive = Join-Path $archiveBase $ConsumerId
$deadletter = Join-Path $base 'deadletter'

if (!(Test-Path $archive)) { New-Item -ItemType Directory -Force -Path $archive | Out-Null }

function Process-Message([string]$filePath) {
  try {
    $content = Get-Content -Raw -Path $filePath | ConvertFrom-Json
    Write-Host "Processing message: $($content.schemaName) id=$($content.id ?? 'N/A')" -ForegroundColor Cyan

    if ($ProcessScript) {
      & $ProcessScript $content
    } else {
      # Simulate processing
      Start-Sleep -Milliseconds 100
    }

    # Success: move to archive
    $name = [IO.Path]::GetFileName($filePath)
    $dest = Join-Path $archive $name
    Move-Item -Force -Path $filePath -Destination $dest
    Write-Host "Archived: $dest" -ForegroundColor Green
  } catch {
    # Failure: move to deadletter
    $name = [IO.Path]::GetFileName($filePath)
    $dest = Join-Path $deadletter $name
    $err = Join-Path $deadletter ($name + '.error.txt')
    Move-Item -Force -Path $filePath -Destination $dest
    Set-Content -Path $err -Value $_.Exception.Message
    Write-Host "Deadlettered: $dest" -ForegroundColor Red
  }
}

if ($Once) {
  $claimed = & $claimScript -Channel $Channel -ConsumerId $ConsumerId -Max $MaxPerLoop
  foreach ($file in $claimed) {
    Process-Message $file
  }
  exit 0
}

while ($true) {
  $claimed = & $claimScript -Channel $Channel -ConsumerId $ConsumerId -Max $MaxPerLoop
  foreach ($file in $claimed) {
    Process-Message $file
  }
  if ($claimed.Count -eq 0) {
    Start-Sleep -Milliseconds $LoopDelayMs
  }
}

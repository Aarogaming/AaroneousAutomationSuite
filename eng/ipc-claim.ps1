param(
  [string]$Root = (Split-Path -Parent $PSScriptRoot),
  [Parameter(Mandatory=$true)][string]$Channel,
  [Parameter(Mandatory=$true)][string]$ConsumerId,
  [int]$Max = 1
)

$ErrorActionPreference = 'Stop'

$repoRoot = [IO.Path]::GetFullPath($Root)
$base = Join-Path $repoRoot "artifacts/ipc/$Channel"
$outbox = Join-Path $base 'outbox'
$processingRoot = Join-Path $base 'processing'
$processing = Join-Path $processingRoot $ConsumerId

if (!(Test-Path $outbox)) { throw "Outbox not found: $outbox" }
if (!(Test-Path $processing)) { New-Item -ItemType Directory -Force -Path $processing | Out-Null }

$claimed = @()
Get-ChildItem -Path $outbox -File -Filter '*.json' | Sort-Object LastWriteTimeUtc | ForEach-Object {
  if ($claimed.Count -ge $Max) { return }
  $src = $_.FullName
  $dest = Join-Path $processing $_.Name
  try {
    Move-Item -Path $src -Destination $dest -ErrorAction Stop
    $claimed += $dest
  } catch {
    # Another consumer likely claimed it.
  }
}

# Print claimed file paths one per line for downstream scripts.
$claimed | ForEach-Object { Write-Output $_ }

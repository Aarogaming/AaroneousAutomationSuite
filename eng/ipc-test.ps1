param(
  [string]$Root = (Split-Path -Parent $PSScriptRoot)
)

$ErrorActionPreference = 'Stop'
$repoRoot = [IO.Path]::GetFullPath($Root)

function Ensure-Dir([string]$p) { if (!(Test-Path $p)) { New-Item -ItemType Directory -Force -Path $p | Out-Null } }

$cmdInbox = Join-Path $repoRoot 'artifacts/ipc/commands/inbox'
$cmdOutbox = Join-Path $repoRoot 'artifacts/ipc/commands/outbox'
$cmdDead = Join-Path $repoRoot 'artifacts/ipc/commands/deadletter'
Ensure-Dir $cmdInbox; Ensure-Dir $cmdOutbox; Ensure-Dir $cmdDead

$snapInbox = Join-Path $repoRoot 'artifacts/ipc/snapshots/inbox'
$snapOutbox = Join-Path $repoRoot 'artifacts/ipc/snapshots/outbox'
$snapDead = Join-Path $repoRoot 'artifacts/ipc/snapshots/deadletter'
Ensure-Dir $snapInbox; Ensure-Dir $snapOutbox; Ensure-Dir $snapDead

$handoffInbox = Join-Path $repoRoot 'artifacts/ipc/handoff/inbox'
$handoffOutbox = Join-Path $repoRoot 'artifacts/ipc/handoff/outbox'
$handoffDead = Join-Path $repoRoot 'artifacts/ipc/handoff/deadletter'
Ensure-Dir $handoffInbox; Ensure-Dir $handoffOutbox; Ensure-Dir $handoffDead

# Clean any prior test files
Get-ChildItem $cmdInbox -Filter 'ipc_test_*' -File -ErrorAction SilentlyContinue | Remove-Item -Force -ErrorAction SilentlyContinue
Get-ChildItem $cmdOutbox -Filter 'ipc_test_*' -File -ErrorAction SilentlyContinue | Remove-Item -Force -ErrorAction SilentlyContinue
Get-ChildItem $cmdDead -Filter 'ipc_test_*' -File -ErrorAction SilentlyContinue | Remove-Item -Force -ErrorAction SilentlyContinue
Get-ChildItem $cmdDead -Filter 'ipc_test_*.error.txt' -File -ErrorAction SilentlyContinue | Remove-Item -Force -ErrorAction SilentlyContinue

Get-ChildItem $snapInbox -Filter 'ipc_test_*' -File -ErrorAction SilentlyContinue | Remove-Item -Force -ErrorAction SilentlyContinue
Get-ChildItem $snapOutbox -Filter 'ipc_test_*' -File -ErrorAction SilentlyContinue | Remove-Item -Force -ErrorAction SilentlyContinue
Get-ChildItem $snapDead -Filter 'ipc_test_*' -File -ErrorAction SilentlyContinue | Remove-Item -Force -ErrorAction SilentlyContinue
Get-ChildItem $snapDead -Filter 'ipc_test_*.error.txt' -File -ErrorAction SilentlyContinue | Remove-Item -Force -ErrorAction SilentlyContinue

Get-ChildItem $handoffInbox -Filter 'ipc_test_*' -File -ErrorAction SilentlyContinue | Remove-Item -Force -ErrorAction SilentlyContinue
Get-ChildItem $handoffOutbox -Filter 'ipc_test_*' -File -ErrorAction SilentlyContinue | Remove-Item -Force -ErrorAction SilentlyContinue
Get-ChildItem $handoffDead -Filter 'ipc_test_*' -File -ErrorAction SilentlyContinue | Remove-Item -Force -ErrorAction SilentlyContinue
Get-ChildItem $handoffDead -Filter 'ipc_test_*.error.txt' -File -ErrorAction SilentlyContinue | Remove-Item -Force -ErrorAction SilentlyContinue

$valid = @{
  schemaName = 'CommandBatch'
  schemaVersion = '1.0.0'
  issuedUtc = (Get-Date).ToUniversalTime().ToString('o')
  commands = @(@{ type='delay'; delayMs=1 })
} | ConvertTo-Json -Depth 10

$invalid = '{ "schemaName": "CommandBatch", "schemaVersion": "1.0.0", "issuedUtc": "2026-01-13T00:00:00Z", "commands": [] }'

$validPath = Join-Path $cmdInbox 'ipc_test_valid.json'
$invalidPath = Join-Path $cmdInbox 'ipc_test_invalid.json'

Set-Content -Path $validPath -Value $valid -Encoding UTF8
Set-Content -Path $invalidPath -Value $invalid -Encoding UTF8

& (Join-Path $repoRoot 'eng/ipc-router.ps1') -Root $repoRoot -Channel commands -Once

if (!(Test-Path (Join-Path $cmdOutbox 'ipc_test_valid.json'))) {
  throw 'Expected valid test message to be routed to outbox'
}
if (!(Test-Path (Join-Path $cmdDead 'ipc_test_invalid.json'))) {
  throw 'Expected invalid test message to be routed to deadletter'
}

# SNAPSHOTS
$snapValid = @{
  schemaName = 'GameStateSnapshot'
  schemaVersion = '1.0.0'
  capturedUtc = (Get-Date).ToUniversalTime().ToString('o')
  resolution = '1280x720'
  gold = 1
} | ConvertTo-Json -Depth 10

$snapInvalid = '{ "schemaName": "GameStateSnapshot", "schemaVersion": "1.0.0" }'

$snapValidPath = Join-Path $snapInbox 'ipc_test_snapshot_valid.json'
$snapInvalidPath = Join-Path $snapInbox 'ipc_test_snapshot_invalid.json'
Set-Content -Path $snapValidPath -Value $snapValid -Encoding UTF8
Set-Content -Path $snapInvalidPath -Value $snapInvalid -Encoding UTF8

& (Join-Path $repoRoot 'eng/ipc-router.ps1') -Root $repoRoot -Channel snapshots -Once

if (!(Test-Path (Join-Path $snapOutbox 'ipc_test_snapshot_valid.json'))) {
  throw 'Expected valid snapshot to be routed to outbox'
}
if (!(Test-Path (Join-Path $snapDead 'ipc_test_snapshot_invalid.json'))) {
  throw 'Expected invalid snapshot to be routed to deadletter'
}

# handoff
$handoffValid = @{
  schemaName = 'HandoffEnvelope'
  schemaVersion = '1.0.0'
  issuedUtc = (Get-Date).ToUniversalTime().ToString('o')
  id = 'ipc_test_handoff_001'
  type = 'command-batch.v1'
  payload = @{
    schemaName = 'CommandBatch'
    schemaVersion = '1.0.0'
    issuedUtc = (Get-Date).ToUniversalTime().ToString('o')
    commands = @(@{ type='delay'; delayMs=1 })
  }
} | ConvertTo-Json -Depth 20

$handoffInvalid = @{
  schemaName = 'HandoffEnvelope'
  schemaVersion = '1.0.0'
  issuedUtc = (Get-Date).ToUniversalTime().ToString('o')
  id = 'ipc_test_handoff_002'
  type = 'command-batch.v1'
  payload = @{
    schemaName = 'CommandBatch'
    schemaVersion = '1.0.0'
    issuedUtc = (Get-Date).ToUniversalTime().ToString('o')
    commands = @()  # invalid for CommandBatch
  }
} | ConvertTo-Json -Depth 20

$handoffValidPath = Join-Path $handoffInbox 'ipc_test_handoff_valid.json'
$handoffInvalidPath = Join-Path $handoffInbox 'ipc_test_handoff_invalid.json'
Set-Content -Path $handoffValidPath -Value $handoffValid -Encoding UTF8
Set-Content -Path $handoffInvalidPath -Value $handoffInvalid -Encoding UTF8

& (Join-Path $repoRoot 'eng/ipc-router.ps1') -Root $repoRoot -Channel handoff -Once

if (!(Test-Path (Join-Path $handoffOutbox 'ipc_test_handoff_valid.json'))) {
  throw 'Expected valid handoff to be routed to outbox'
}
if (!(Test-Path (Join-Path $handoffDead 'ipc_test_handoff_invalid.json'))) {
  throw 'Expected invalid handoff to be routed to deadletter (payload invalid)'
}

# CONSUMER LOOP TEST
$consumerId = 'testConsumer'
$loopTestFile = Join-Path $cmdOutbox 'ipc_test_loop.json'
$loopContent = @{
  schemaName = 'CommandBatch'
  schemaVersion = '1.0.0'
  issuedUtc = (Get-Date).ToUniversalTime().ToString('o')
  commands = @(@{ type='delay'; delayMs=1 })
} | ConvertTo-Json -Depth 10

Set-Content -Path $loopTestFile -Value $loopContent -Encoding UTF8

& (Join-Path $repoRoot 'eng/ipc-consumer-loop.ps1') -Channel commands -ConsumerId $consumerId -Once

$archive = Join-Path $repoRoot "artifacts/ipc/commands/archive/$consumerId"
if (!(Test-Path (Join-Path $archive 'ipc_test_loop.json'))) {
  throw 'Expected loop test message to be archived'
}

Write-Host 'IPC router test OK' -ForegroundColor Green

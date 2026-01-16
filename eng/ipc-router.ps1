param(
  [string]$Root = (Split-Path -Parent $PSScriptRoot),
  [string]$Channel = "*",
  [switch]$Once
)

$ErrorActionPreference = 'Stop'

function Get-ChannelPaths([string]$repoRoot, [string]$channelName) {
  $base = Join-Path $repoRoot "artifacts/ipc/$channelName"
  return [pscustomobject]@{
    Base = $base
    Inbox = Join-Path $base 'inbox'
    Outbox = Join-Path $base 'outbox'
    Deadletter = Join-Path $base 'deadletter'
  }
}

function Validate-FileWithSchema([string]$schemaFile, [string]$filePath) {
  if (!(Test-Path $toolProject)) {
    return @{ ok = $false; reason = 'toolkit-missing' }
  }
  try {
    & dotnet run --project $toolProject -c Release -- contracts checkfile --root $repoRoot --schema $schemaFile --file $filePath | Out-Null
    if ($LASTEXITCODE -eq 0) {
      return @{ ok = $true }
    }
    return @{ ok = $false; reason = "schema-validation-failed ($schemaFile)" }
  } catch {
    return @{ ok = $false; reason = $_.Exception.Message }
  }
}

function Ensure-Dirs($paths) {
  foreach ($p in @($paths.Inbox,$paths.Outbox,$paths.Deadletter)) {
    if (!(Test-Path $p)) { New-Item -ItemType Directory -Force -Path $p | Out-Null }
  }
}

function Deadletter-File([string]$filePath, $paths, [string]$reason) {
  $name = [IO.Path]::GetFileName($filePath)
  $dest = Join-Path $paths.Deadletter $name
  $err = Join-Path $paths.Deadletter ($name + '.error.txt')
  Move-Item -Force -Path $filePath -Destination $dest
  Set-Content -Path $err -Value $reason
}

function Accept-File([string]$filePath, $paths) {
  $name = [IO.Path]::GetFileName($filePath)
  $dest = Join-Path $paths.Outbox $name
  Move-Item -Force -Path $filePath -Destination $dest
}

function Validate-JsonLight([string]$filePath) {
  try {
    $text = Get-Content -Raw -Path $filePath
    $obj = $text | ConvertFrom-Json
    if ($null -eq $obj.schemaName -or $null -eq $obj.schemaVersion) {
      return @{ ok = $false; reason = 'Missing schemaName/schemaVersion' }
    }
    return @{ ok = $true; schemaName = [string]$obj.schemaName; schemaVersion = [string]$obj.schemaVersion }
  } catch {
    return @{ ok = $false; reason = $_.Exception.Message }
  }
}

$repoRoot = [IO.Path]::GetFullPath($Root)
$toolProject = Join-Path $repoRoot "Workbench\Tools\MaelstromToolkit\MaelstromToolkit.csproj"
$toolDll = Join-Path $repoRoot "Workbench\Tools\MaelstromToolkit\bin\Release\net8.0\MaelstromToolkit.dll"

function Get-SchemaForChannel([string]$channelName) {
  switch ($channelName.ToLowerInvariant()) {
    'commands' { return 'command-batch.v1.schema.json' }
    'snapshots' { return 'snapshot.v1.schema.json' }
    'handoff' { return 'handoff-envelope.v1.schema.json' }
    default { return '' }
  }
}

function Get-PayloadSchemaForHandoffType([string]$handoffType) {
  switch ($handoffType.ToLowerInvariant()) {
    'command-batch.v1' { return 'command-batch.v1.schema.json' }
    'snapshot.v1' { return 'snapshot.v1.schema.json' }
    default { return '' }
  }
}

function Validate-HandoffPayload([string]$filePath) {
  try {
    $text = Get-Content -Raw -Path $filePath
    $obj = $text | ConvertFrom-Json
    if ($null -eq $obj.type) {
      return @{ ok = $false; reason = 'handoff missing type' }
    }
    $schema = Get-PayloadSchemaForHandoffType ([string]$obj.type)
    if ([string]::IsNullOrWhiteSpace($schema)) {
      return @{ ok = $true; skipped = $true }
    }

    # Write payload to temp file and validate against mapped schema
    $tmp = [IO.Path]::Combine([IO.Path]::GetTempPath(), "aas_ipc_payload_" + [guid]::NewGuid().ToString('N') + ".json")
    try {
      $payloadJson = $obj.payload | ConvertTo-Json -Depth 20
      Set-Content -Path $tmp -Value $payloadJson -Encoding UTF8
      $res = Validate-FileWithSchema $schema $tmp
      if ($res.ok) { return @{ ok = $true } }
      return @{ ok = $false; reason = 'payload schema validation failed' }
    }
    finally {
      try { if (Test-Path $tmp) { Remove-Item -Force $tmp } } catch {}
    }
  }
  catch {
    return @{ ok = $false; reason = $_.Exception.Message }
  }
}

function Validate-WithToolkit([string]$channelName, [string]$filePath) {
  if (!(Test-Path $toolProject)) {
    return @{ ok = $false; reason = 'toolkit-missing' }
  }

  $schema = Get-SchemaForChannel $channelName
  if ([string]::IsNullOrWhiteSpace($schema)) {
    return @{ ok = $false; reason = 'unknown-channel-schema' }
  }

  try {
    if (Test-Path $toolDll) {
      & dotnet $toolDll contracts checkfile --root $repoRoot --schema $schema --file $filePath | Out-Null
    } else {
      & dotnet run --project $toolProject -c Release -- contracts checkfile --root $repoRoot --schema $schema --file $filePath | Out-Null
    }
    if ($LASTEXITCODE -eq 0) {
      return @{ ok = $true }
    }
    return @{ ok = $false; reason = "schema-validation-failed ($schema)" }
  } catch {
    return @{ ok = $false; reason = $_.Exception.Message }
  }
}

Write-Host "IPC router root=$repoRoot channel=$Channel" -ForegroundColor Cyan

$channels = @('commands','snapshots','handoff')
if ($Channel -ne '*') {
  $channels = $channels | Where-Object { $_ -ieq $Channel }
}

foreach ($ch in $channels) {
  $paths = Get-ChannelPaths $repoRoot $ch
  Ensure-Dirs $paths
}

function Process-Channel([string]$ch) {
  $paths = Get-ChannelPaths $repoRoot $ch
  Ensure-Dirs $paths

  Get-ChildItem -Path $paths.Inbox -File -Filter '*.json' | ForEach-Object {
    $file = $_.FullName
    $check = Validate-JsonLight $file
    if (-not $check.ok) {
      Deadletter-File $file $paths ("Invalid JSON: " + $check.reason)
      return
    }

    $full = Validate-WithToolkit $ch $file
    if ($full.ok) {
      if ($ch -ieq 'handoff') {
        $payloadRes = Validate-HandoffPayload $file
        if (-not $payloadRes.ok) {
          Deadletter-File $file $paths ("Handoff payload invalid: " + $payloadRes.reason)
          return
        }
      }
      Accept-File $file $paths
      return
    }

    if ($full.reason -eq 'toolkit-missing') {
      # Fallback: accept light-validated messages if toolkit isn't present.
      Accept-File $file $paths
      return
    }

    Deadletter-File $file $paths ("Schema validation failed: " + $full.reason)
  }
}

if ($Once) {
  foreach ($ch in $channels) { Process-Channel $ch }
  exit 0
}

while ($true) {
  foreach ($ch in $channels) { Process-Channel $ch }
  Start-Sleep -Milliseconds 250
}

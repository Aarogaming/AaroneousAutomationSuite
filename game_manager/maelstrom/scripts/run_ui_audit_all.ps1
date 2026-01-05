param(
    [string]$ConfigPath = "DevTools/UiAuditRunner/config.json",
    [int[]]$Dpis = @(100,125,150,175)
)

Set-StrictMode -Version Latest
$ErrorActionPreference = "Stop"

if (-not (Test-Path $ConfigPath)) {
    Write-Error "Config file not found: $ConfigPath"
    exit 1
}

function Update-DpiLabel {
    param($Path, $Dpi)
    $json = Get-Content $Path -Raw | ConvertFrom-Json
    $json.dpiLabel = "$Dpi"
    ($json | ConvertTo-Json -Depth 10) | Set-Content $Path -Encoding UTF8
}

$results = @()

foreach ($dpi in $Dpis) {
    Write-Host "=== UI Audit for DPI $dpi% ==="
    Write-Host "Set Windows display scale to $dpi% now, then press Enter to continue."
    Read-Host | Out-Null

    Update-DpiLabel -Path $ConfigPath -Dpi $dpi

    Write-Host "Running UiAuditRunner..."
    dotnet run --project DevTools/UiAuditRunner/UiAuditRunner.csproj -- $ConfigPath

    $zipName = "ui_audit_pack_$dpi.zip"
    $zipPath = Join-Path (Get-Location) $zipName
    if (Test-Path $zipPath) {
        Write-Host "Created: $zipPath"
        $results += @{ Dpi = $dpi; Path = $zipPath }
    } else {
        Write-Warning "Zip not found for DPI $dpi"
        $results += @{ Dpi = $dpi; Path = "<missing>" }
    }
}

Write-Host "`n=== Summary ==="
foreach ($r in $results) {
    Write-Host ("DPI {0}: {1}" -f $r.Dpi, $r.Path)
}

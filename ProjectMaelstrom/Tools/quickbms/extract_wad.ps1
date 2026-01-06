Param(
    [Parameter(Mandatory = $true, Position = 0)]
    [string[]] $WadPath,

    [Parameter(Mandatory = $true, Position = 1)]
    [string] $OutputDir,

    [string] $QuickBmsExe = "$PSScriptRoot\quickbms.exe",
    [string] $BmsScript = "$PSScriptRoot\wizard101_kiwad.bms",
    [switch] $Force
)

if (-not (Test-Path $QuickBmsExe)) {
    Write-Error "quickbms.exe not found at $QuickBmsExe"
    exit 1
}
if (-not (Test-Path $BmsScript)) {
    Write-Error "BMS script not found at $BmsScript"
    exit 1
}

$outRoot = Resolve-Path $OutputDir -ErrorAction SilentlyContinue
if (-not $outRoot) {
    $null = New-Item -ItemType Directory -Path $OutputDir -Force
    $outRoot = Resolve-Path $OutputDir
}

foreach ($wad in $WadPath) {
    if (-not (Test-Path $wad)) {
        Write-Warning "WAD not found: $wad"
        continue
    }
    $wadFull = Resolve-Path $wad
    $dest = Join-Path $outRoot ($wadFull.BaseName)

    if ((Test-Path $dest) -and -not $Force) {
        Write-Host "Skipping (exists): $dest (use -Force to overwrite)" -ForegroundColor Yellow
        continue
    }

    $null = New-Item -ItemType Directory -Path $dest -Force
    Write-Host "Extracting $wadFull -> $dest"

    $psi = New-Object System.Diagnostics.ProcessStartInfo
    $psi.FileName = $QuickBmsExe
    $psi.ArgumentList = @('-Y', $BmsScript, $wadFull, $dest)
    $psi.UseShellExecute = $false
    $psi.RedirectStandardOutput = $true
    $psi.RedirectStandardError = $true

    $proc = New-Object System.Diagnostics.Process
    $proc.StartInfo = $psi
    $proc.Start() | Out-Null
    $stdout = $proc.StandardOutput.ReadToEnd()
    $stderr = $proc.StandardError.ReadToEnd()
    $proc.WaitForExit()

    if ($proc.ExitCode -ne 0) {
        Write-Warning "QuickBMS failed for $wadFull (code $($proc.ExitCode))"
        if ($stdout) { Write-Host $stdout }
        if ($stderr) { Write-Error $stderr }
    }
}

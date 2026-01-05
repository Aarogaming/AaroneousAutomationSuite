param(
    [double]$Threshold = 0.5,
    [switch]$Portable
)

Set-StrictMode -Version Latest
$ErrorActionPreference = "Stop"

$scriptDir = Split-Path -Parent $MyInvocation.MyCommand.Path
$repoRoot = Resolve-Path (Join-Path $scriptDir "..")
Set-Location $repoRoot

# Hint tessdata for UiAuditSelfCapture
$tessdata = Join-Path $repoRoot "tessdata"
if (Test-Path $tessdata) {
    $env:TESSDATA_PREFIX = $tessdata
}

$steps = New-Object System.Collections.Generic.List[object]
$results = New-Object System.Collections.Generic.List[object]

function Add-Step {
    param(
        [string]$Name,
        [scriptblock]$Action
    )
    $steps.Add([pscustomobject]@{ Name = $Name; Action = $Action })
}

function Invoke-Step {
    param(
        [pscustomobject]$Step
    )

    Write-Host "== $($Step.Name) =="
    try {
        & $Step.Action
        $exitCode = $LASTEXITCODE
        if ($exitCode -ne $null -and $exitCode -ne 0) {
            throw "Exit code $exitCode"
        }
        $results.Add([pscustomobject]@{ Name = $Step.Name; Status = "PASS"; Details = "" })
        return $true
    }
    catch {
        $results.Add([pscustomobject]@{ Name = $Step.Name; Status = "FAIL"; Details = $_.Exception.Message })
        Write-Error "$($Step.Name) failed: $($_.Exception.Message)"
        return $false
    }
}

Add-Step "Build (Debug)" {
    dotnet build ProjectMaelstrom/ProjectMaelstrom.sln -c Debug
}

Add-Step "UI Regression Check" {
    powershell -ExecutionPolicy Bypass -File "./scripts/ui_check_regression.ps1" -Threshold $Threshold
}

Add-Step "Functional Tests" {
    dotnet run --project DevTools/FunctionalTestRunner/FunctionalTestRunner.csproj
}

Add-Step "Secret Scan" {
    powershell -ExecutionPolicy Bypass -File "./scripts/scan_for_secrets.ps1" -Path "." -Extensions ".cs,.ps1,.md,.json,.txt,.yml,.yaml,.config,.htm,.html,.js"
}

if ($Portable.IsPresent) {
    Add-Step "Portable Build" {
        powershell -ExecutionPolicy Bypass -File "./scripts/build_portable.ps1"
    }
}

$failed = $false

for ($i = 0; $i -lt $steps.Count; $i++) {
    $step = $steps[$i]
    if (-not (Invoke-Step $step)) {
        $failed = $true
        for ($j = $i + 1; $j -lt $steps.Count; $j++) {
            $results.Add([pscustomobject]@{
                Name    = $steps[$j].Name
                Status  = "SKIPPED"
                Details = "Not run due to prior failure"
            })
        }
        break
    }
}

Write-Host ""
Write-Host "==== Final Verification Summary ===="
foreach ($r in $results) {
    $color = switch ($r.Status) {
        "PASS" { "Green" }
        "FAIL" { "Red" }
        default { "Yellow" }
    }
    Write-Host ("{0,-30} {1}" -f $r.Name, $r.Status) -ForegroundColor $color
    if ($r.Details) {
        Write-Host ("  -> {0}" -f $r.Details)
    }
}

if ($failed) {
    exit 1
}

exit 0

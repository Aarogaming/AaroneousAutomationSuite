[CmdletBinding()]
param()

function Test-ChecksumFile {
    param(
        [Parameter(Mandatory = $true)][string]$Path
    )
    $result = [pscustomobject]@{
        File      = $Path
        Parsed    = 0
        Matched   = 0
        Missing   = 0
        Mismatch  = 0
        Status    = "PASS"
        Details   = @()
    }

    if (-not (Test-Path $Path)) {
        $result.Status = "FAIL (missing checksum file)"
        return $result
    }

    $regex = '^\s*(?<Algorithm>\S+)\s+(?<Hash>[A-Fa-f0-9]{64})\s+(?<Path>.+)$'
    foreach ($line in Get-Content -LiteralPath $Path) {
        if ([string]::IsNullOrWhiteSpace($line)) { continue }
        if ($line -match '^\s*-{2,}') { continue }
        if ($line -match '^\s*Algorithm\s+Hash\s+Path') { continue }
        $m = [regex]::Match($line, $regex)
        if (-not $m.Success) { continue }
        $result.Parsed++
        $targetPath = $m.Groups['Path'].Value.Trim()
        $algo = $m.Groups['Algorithm'].Value.Trim()
        $expected = $m.Groups['Hash'].Value.Trim()
        if (-not (Test-Path $targetPath)) {
            $result.Missing++
            $result.Details += "Missing: $targetPath"
            continue
        }
        try {
            $actual = (Get-FileHash -LiteralPath $targetPath -Algorithm $algo).Hash
            if ($actual.Equals($expected, [System.StringComparison]::OrdinalIgnoreCase)) {
                $result.Matched++
            } else {
                $result.Mismatch++
                $result.Details += "Mismatch: $targetPath"
            }
        } catch {
            $result.Mismatch++
            $result.Details += "Error hashing: $targetPath -> $($_.Exception.Message)"
        }
    }

    if ($result.Parsed -eq 0) {
        $result.Status = "FAIL (no entries parsed)"
    } elseif ($result.Missing -gt 0 -or $result.Mismatch -gt 0) {
        $result.Status = "FAIL"
    }
    return $result
}

function Test-RequiredFiles {
    param(
        [Parameter(Mandatory = $true)][string[]]$Paths
    )
    $missing = @()
    foreach ($p in $Paths) {
        if (-not (Test-Path $p)) {
            $missing += $p
        }
    }
    return $missing
}

$requiredArtifacts = @(
    "artifacts/submission/final_verify_report.txt",
    "artifacts/submission/ui_diff_report.txt",
    "artifacts/submission/functional_test_runner.txt",
    "artifacts/submission/secret_scan.txt",
    "artifacts/submission/checksums_portable.txt",
    "artifacts/submission/checksums_submission.txt",
    "artifacts/submission/reviewer_bundle_manual.zip",
    "artifacts/submission/INDEX.txt",
    "artifacts/submission/REPRO_STAMP.txt"
)

$checksumFiles = @(
    "artifacts/submission/checksums_portable.txt",
    "artifacts/submission/checksums_submission.txt"
)

$missing = Test-RequiredFiles -Paths $requiredArtifacts
$checksumResults = @()
foreach ($cs in $checksumFiles) {
    $checksumResults += Test-ChecksumFile -Path $cs
}

$fail = $false
if ($missing.Count -gt 0) { $fail = $true }
if ($checksumResults | Where-Object { $_.Status -like "FAIL*" }) { $fail = $true }

Write-Host "=== Reviewer Verify ==="
if ($missing.Count -gt 0) {
    Write-Host "Missing artifacts:" -ForegroundColor Yellow
    $missing | ForEach-Object { Write-Host " - $_" }
} else {
    Write-Host "All required artifacts present." -ForegroundColor Green
}

foreach ($r in $checksumResults) {
    Write-Host "$($r.File): $($r.Status) (parsed=$($r.Parsed), matched=$($r.Matched), missing=$($r.Missing), mismatch=$($r.Mismatch))"
    foreach ($d in $r.Details) {
        Write-Host "  $d"
    }
}

if ($fail) {
    Write-Host "Reviewer verify: FAIL" -ForegroundColor Red
    exit 1
}

Write-Host "Reviewer verify: PASS" -ForegroundColor Green
exit 0

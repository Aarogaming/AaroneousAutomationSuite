param(
    [string]$Path = ".",
    [string[]]$Extensions = @(".cs",".ps1",".md",".json",".txt",".yml",".yaml",".config",".htm",".html",".js"),
    [int]$MaxMatches = 50
)

Set-StrictMode -Version Latest
$ErrorActionPreference = "Stop"

function Matches-Secret {
    param($line)
    $patterns = @(
        "ghp_[A-Za-z0-9]+",
        "AIza[0-9A-Za-z\-_]{20,}",
        "-----BEGIN PRIVATE KEY-----",
        "BEGIN RSA PRIVATE KEY"
    )
    foreach ($p in $patterns) {
        if ($line -match $p) { return $true }
    }
    return $false
}

$matches = @()

Get-ChildItem -Path $Path -Recurse -File | Where-Object {
    $Extensions -contains $_.Extension
} | ForEach-Object {
    $file = $_.FullName
    $i = 0
    Get-Content $file | ForEach-Object {
        $i++
        if (Matches-Secret $_) {
            $matches += [pscustomobject]@{
                File = $file
                Line = $i
                Text = $_
            }
            if ($matches.Count -ge $MaxMatches) { break }
        }
    }
}

if ($matches.Count -eq 0) {
    Write-Host "No secrets detected." -ForegroundColor Green
    exit 0
}

Write-Host "Potential secrets found:" -ForegroundColor Yellow
foreach ($m in $matches) {
    Write-Host ("{0}:{1}: {2}" -f $m.File, $m.Line, $m.Text)
}

Write-Host "If matches are third-party assets, redact or vendor them; do not commit real secrets." -ForegroundColor Yellow
exit 1

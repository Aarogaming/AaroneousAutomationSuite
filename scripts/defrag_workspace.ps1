# Workspace Defragmentation and Restructuring Script
# Purpose: Consolidate and simplify the AAS directory structure

Write-Host "=== AAS Workspace Defragmentation ===" -ForegroundColor Cyan
Write-Host ""

$results = @()

# 1. Remove duplicate AutoWizard101 at root (keep game_manager/maelstrom version)
if (Test-Path "AutoWizard101") {
    $rootSize = (Get-ChildItem "AutoWizard101" -Recurse -File | Measure-Object -Property Length -Sum).Sum / 1MB
    Write-Host "Found AutoWizard101 at root ($([math]::Round($rootSize, 2)) MB)" -ForegroundColor Yellow
    
    # Check if it's truly duplicate
    if (Test-Path "game_manager/maelstrom/AutoWizard101") {
        Write-Host "  Comparing with game_manager/maelstrom/AutoWizard101..." -ForegroundColor Gray
        $rootREADME = Get-FileHash "AutoWizard101/README.md" -ErrorAction SilentlyContinue
        $gameREADME = Get-FileHash "game_manager/maelstrom/AutoWizard101/README.md" -ErrorAction SilentlyContinue
        
        if ($rootREADME.Hash -eq $gameREADME.Hash) {
            Write-Host "  DUPLICATE CONFIRMED - Removing root copy" -ForegroundColor Green
            Remove-Item "AutoWizard101" -Recurse -Force
            $results += "Removed duplicate AutoWizard101 (saved $([math]::Round($rootSize, 2)) MB)"
        } else {
            Write-Host "  FILES DIFFER - Manual review needed" -ForegroundColor Red
            $results += "WARNING: AutoWizard101 versions differ - kept both"
        }
    }
}

# 2. Consolidate game_manager build outputs
if (Test-Path "game_manager/maelstrom/publish") {
    $pubSize = (Get-ChildItem "game_manager/maelstrom/publish" -Recurse -File | Measure-Object -Property Length -Sum).Sum / 1MB
    Write-Host "`nFound publish directory ($([math]::Round($pubSize, 2)) MB)" -ForegroundColor Yellow
    Write-Host "  Moving to artifacts/builds/" -ForegroundColor Gray
    
    New-Item -ItemType Directory -Path "artifacts/builds" -Force | Out-Null
    Move-Item "game_manager/maelstrom/publish" -Destination "artifacts/builds/maelstrom_publish" -Force
    $results += "Moved game_manager/maelstrom/publish -> artifacts/builds/"
}

# 3. Consolidate UI audit directories
$uiDirs = @("game_manager/maelstrom/ui_audit_pack_selfcapture", "game_manager/maelstrom/ui_baseline", "game_manager/maelstrom/ui_current")
$totalUISize = 0
foreach ($dir in $uiDirs) {
    if (Test-Path $dir) {
        $size = (Get-ChildItem $dir -Recurse -File | Measure-Object -Property Length -Sum).Sum / 1MB
        $totalUISize += $size
    }
}

if ($totalUISize -gt 0) {
    Write-Host "`nFound UI audit directories ($([math]::Round($totalUISize, 2)) MB total)" -ForegroundColor Yellow
    Write-Host "  Moving to artifacts/ui_audits/" -ForegroundColor Gray
    
    New-Item -ItemType Directory -Path "artifacts/ui_audits" -Force | Out-Null
    foreach ($dir in $uiDirs) {
        if (Test-Path $dir) {
            $dirName = Split-Path $dir -Leaf
            Move-Item $dir -Destination "artifacts/ui_audits/$dirName" -Force
        }
    }
    $results += "Moved UI audit directories -> artifacts/ui_audits/"
}

# 4. Clean up empty plugin directories
Write-Host "`nChecking plugins..." -ForegroundColor Yellow
Get-ChildItem "plugins" -Directory | ForEach-Object {
    $fileCount = (Get-ChildItem $_.FullName -Recurse -File).Count
    if ($fileCount -eq 0) {
        Write-Host "  Removing empty plugin: $($_.Name)" -ForegroundColor Gray
        Remove-Item $_.FullName -Recurse -Force
        $results += "Removed empty plugin: $($_.Name)"
    }
}

# 5. Consolidate scattered documentation
Write-Host "`nConsolidating documentation..." -ForegroundColor Yellow
$docFiles = Get-ChildItem "game_manager/maelstrom" -File -Filter "*.md"
if ($docFiles.Count -gt 0) {
    New-Item -ItemType Directory -Path "docs/maelstrom" -Force | Out-Null
    $docFiles | ForEach-Object {
        Copy-Item $_.FullName -Destination "docs/maelstrom/$($_.Name)" -Force
        Write-Host "  Copied: $($_.Name)" -ForegroundColor Gray
    }
    $results += "Consolidated $($docFiles.Count) Maelstrom docs -> docs/maelstrom/"
}

# 6. Summary
Write-Host "`n=== RESTRUCTURING COMPLETE ===" -ForegroundColor Green
Write-Host ""
$results | ForEach-Object { Write-Host "  - $_" -ForegroundColor White }

Write-Host "`n=== SIMPLIFIED STRUCTURE ===" -ForegroundColor Cyan
Write-Host ""
Write-Host "Core Directories:" -ForegroundColor White
Write-Host "  artifacts/          - All build outputs, reports, UI audits" -ForegroundColor Gray
Write-Host "  core/               - AAS Hub core components" -ForegroundColor Gray
Write-Host "  docs/               - All documentation" -ForegroundColor Gray
Write-Host "  game_manager/       - Game automation logic" -ForegroundColor Gray
Write-Host "  plugins/            - Active plugins only" -ForegroundColor Gray
Write-Host "  scripts/            - Utility scripts" -ForegroundColor Gray
Write-Host "  Wizard101_DanceBot/ - Standalone project" -ForegroundColor Gray
Write-Host ""
Write-Host "Workspace is now defragmented!" -ForegroundColor Green

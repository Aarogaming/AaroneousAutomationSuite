# Fetch Wizard101 official world pages to local HTML for offline reference.
# Usage:
#   powershell -ExecutionPolicy Bypass -File tools/wizard101_world_fetch.ps1
#
# Output:
#   Saves HTML files to ProjectMaelstrom/Scripts/Library/WizWikiAPI-main/worlds_raw/

$worldUrls = @(
    "https://www.wizard101.com/game/worlds/wizardcity",
    "https://www.wizard101.com/game/worlds/krokotopia",
    "https://www.wizard101.com/game/worlds/marleybone",
    "https://www.wizard101.com/game/worlds/mooshu",
    "https://www.wizard101.com/game/worlds/dragonspyre",
    "https://www.wizard101.com/game/worlds/celestia",
    "https://www.wizard101.com/game/worlds/zafaria",
    "https://www.wizard101.com/game/worlds/avalon",
    "https://www.wizard101.com/game/worlds/azteca",
    "https://www.wizard101.com/game/worlds/khrysalis",
    "https://www.wizard101.com/game/worlds/polaris",
    "https://www.wizard101.com/game/worlds/mirage",
    "https://www.wizard101.com/game/worlds/empyea"
)

$outDir = Join-Path -Path (Split-Path -Parent $PSScriptRoot) -ChildPath "ProjectMaelstrom\Scripts\Library\WizWikiAPI-main\worlds_raw"
New-Item -ItemType Directory -Force -Path $outDir | Out-Null

foreach ($url in $worldUrls) {
    try {
        $fileSafe = ($url -replace '[^a-zA-Z0-9_-]', '_') + ".html"
        $target = Join-Path $outDir $fileSafe
        Write-Host "Fetching $url -> $target"
        $resp = Invoke-WebRequest -Uri $url -UseBasicParsing
        $resp.Content | Out-File -FilePath $target -Encoding UTF8
    } catch {
        Write-Warning "Failed to fetch $url : $_"
    }
}

Write-Host "Done. Pages saved under $outDir." -ForegroundColor Green

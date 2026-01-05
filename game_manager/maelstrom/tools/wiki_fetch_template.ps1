# Fetch Wizard101 wiki pages to local JSON/HTML for offline ingestion.
# Usage:
# 1) Edit the $pages list below to include full URLs to the wiki pages you want (zones, resources, NPCs, quests, crafting, etc.).
# 2) Run: powershell -ExecutionPolicy Bypass -File tools/wiki_fetch_template.ps1
# 3) Outputs land in Scripts/Library/WizWikiAPI-main/wiki_fetch_raw

$pages = @(
    # Example (replace with the specific pages you need):
    # "https://wizard101.fandom.com/wiki/Wizard_City",
    # "https://wizard101.fandom.com/wiki/Reagents",
    # "https://wizard101.fandom.com/wiki/Quests"
)

if ($pages.Count -eq 0) {
    Write-Host "No pages specified. Edit tools/wiki_fetch_template.ps1 and add wiki URLs to `$pages." -ForegroundColor Yellow
    exit 1
}

$outDir = Join-Path -Path (Split-Path -Parent $PSScriptRoot) -ChildPath "ProjectMaelstrom\Scripts\Library\WizWikiAPI-main\wiki_fetch_raw"
New-Item -ItemType Directory -Force -Path $outDir | Out-Null

$session = New-Object Microsoft.PowerShell.Commands.WebRequestSession

foreach ($url in $pages) {
    try {
        $fileSafe = ($url -replace '[^a-zA-Z0-9_-]', '_')
        $target = Join-Path $outDir "$fileSafe.html"
        Write-Host "Fetching $url -> $target"
        $resp = Invoke-WebRequest -Uri $url -WebSession $session -UseBasicParsing
        $resp.Content | Out-File -FilePath $target -Encoding UTF8
    } catch {
        Write-Warning "Failed to fetch $url : $_"
    }
}

Write-Host "Done. Raw pages saved under $outDir. Next: convert them to structured JSON (zones/resources/NPCs/quests) for the app to ingest." -ForegroundColor Green

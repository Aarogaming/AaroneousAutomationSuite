# Aaroneous Automation Suite
[![CI](https://github.com/Aarogaming/aaroneous-automation-suite/actions/workflows/ci.yml/badge.svg?branch=main)](https://github.com/Aarogaming/aaroneous-automation-suite/actions/workflows/ci.yml)

Wizard101 automation toolkit with bots, OCR-driven utilities, and a script runner that can load community scripts from a shared library folder.

### DevTools and handoff helpers
- Handoff bridge & toolkit: see `HANDOFF_BRIDGE_SPEC.md`, `COOP_WORKFLOW.md`, `TEMPLATE_SYSTEM.md`.
- Tray + watcher helper (Windows only, default OFF): `docs/HandoffTray.md`.
- Toolkit selftest: `dotnet run --project MaelstromToolkit/MaelstromToolkit.csproj -- selftest`.

### Docs
- Project context and endpoints: `docs/ASSISTANT_CONTEXT.md`
- Demo script: `docs/DEMO_SCRIPT.md`
- Roadmap: `docs/ROADMAP.md`
- Troubleshooting: `docs/TROUBLESHOOTING.md`
- Session log: `docs/COOP_PACKET.md`

## Version Support / Policy
- Current target: net9.0-windows10.0.22621.0
- Profiles: Public and Experimental; live automation is controlled via the `ALLOW_LIVE_AUTOMATION` flag.
- Portable builds exclude DevTools; sample plugins included only when explicitly requested.
- Audit readiness: GOLD_FREEZE.md, AUDIT_TRAIL.md, MAINTENANCE.md capture policy, checks, and freeze state.

### Runtime guards (enforced)
- Policy load: `ExecutionPolicyManager` reads `execution_policy.conf`; defaults are safe (`ALLOW_LIVE_AUTOMATION=false`, `EXECUTION_PROFILE=AcademicSimulation`).
- Executor selection: `ExecutorFactory` / `LiveExecutor` block live dispatch when live is disabled.
- Plugin gating: `Plugins.Evaluate` blocks `LiveIntegration` capability when live is disabled or profile is AcademicSimulation.
- Input/Macro bridges: `InputBridge` and `MacroPlayer` block command dispatch when live is disabled.
- Settings shows the active policy snapshot (Allow, Mode, Path, Loaded UTC, backend info).

### Not enforced (planned)
- Additional sandboxing or stricter separation would require future code changes; not active today.

## Highlights
- WinForms app (C# / .NET 9) with ready-made bots: Halfang farming, Bazaar reagent buying, Pet Dance launcher.
- Image + OCR pipeline (Emgu CV + Tesseract) for detecting UI elements and reading stats.
- Script Library: drop scripts into `ProjectMaelstrom/ProjectMaelstrom/Scripts/Library/<name>` with a `manifest.json`, then run/stop from the UI.
- Sync indicator shows whether the game window is present, focused, and at the expected resolution.
- Theme toggle: choose between system theme and a Wizard101-inspired palette in Settings.
- Wizard theme palette lives in `ProjectMaelstrom/ProjectMaelstrom/wizard_palette.json` (copied to output). Edit hex colors there to match captured game UI; the app reloads it on launch when the Wizard101 theme is selected.
- Snapshot bridge: the app writes OCR’d snapshots to `Scripts/.cache/snapshot.json` every ~5s so external scripts can read health/mana/gold/sync status without redoing OCR.
- Input bridge: when enabled, the app polls `Scripts/.cache/commands.json` and executes commands (clicks/keys) via the trainer. Format example:
  ```json
  [
    {"type": "click", "x": 500, "y": 400},
    {"type": "key_press", "key": "SPACE", "delayMs": 200}
  ]
  ```
- See `ProjectMaelstrom/ProjectMaelstrom/Scripts/Library/BRIDGES.md` and `commands_example.json` for usage patterns.

## Requirements
- Windows 10/11
- .NET 9.0 Runtime
- Wizard101 installed and running in windowed mode
- OCR.space API key (free tier works)

## Quickstart (Release ZIP)
1) Download the latest release ZIP from the Releases page.
2) Extract and run `ProjectMaelstrom.exe`.
3) Set your game to 1280x720 (or your chosen supported resolution).
4) Open Settings in the app, paste your OCR.space API key, and save.
5) Use the main buttons to launch a bot, or open the Script Library panel to run a custom script.

## Quickstart (Source)
```powershell
git clone https://github.com/yourusername/aaroneous-automation-suite.git
cd aaroneous-automation-suite/ProjectMaelstrom
dotnet restore
dotnet build --configuration Release
dotnet run --project ProjectMaelstrom
```

## Script Library
- Location: `ProjectMaelstrom/ProjectMaelstrom/Scripts/Library`.
- Each script folder needs a `manifest.json`:
  ```json
  {
    "name": "Sample Echo",
    "description": "Tiny sample script that logs a message.",
    "author": "OriginalAuthorHandle",
    "entryPoint": "run.bat",
    "arguments": "",
    "sourceUrl": "https://github.com/user/repo",
    "requiredResolution": "1280x720",
    "requiredTemplates": []
  }
  ```
- Entry point can be an `.exe`, `.bat`, or other runnable file. It runs with working directory set to the script folder.
- Validation warnings (missing entry point, resolution mismatch, missing assets) are shown in the UI before run.
- Logs per script are written to `logs/<script>.log`.
- Raid utilities are split into individual entries: `raid-az-tool`, `raid-ds-tool`, `raid-lm-tool`, `raid-pl-tool` (they point to their respective `main.py` under `raid-utility-tools-main`).

## Bots
- Halfang Dungeon Bot: Fire wizard (Meteor) at 1280x720; automates dungeon entry/combat loop.
- Bazaar Reagent Bot: Select reagents and auto-purchase in the bazaar at 1280x720.
- Pet Dance: Launches an external PetDance script/exe.

## Sync Indicator
- Green: Window present, focused, and matches the configured resolution.
- Orange: Focus lost or resolution mismatch.
- Red: Window missing or sync check failed.

## Game State Snapshots (OCR)
- Game stats (health/mana/gold) are OCR’d from defined regions per resolution.
- ROI config lives at `ProjectMaelstrom/ProjectMaelstrom/Resources/<resolution>/rois.json` (normalized coordinates). Tweak these if OCR is off.
- Snapshots are consumed by the script runner and future overlays/debug views.

## Troubleshooting
- “Window not found”: ensure Wizard101 is running, windowed, and visible; try running the app as admin.
- OCR errors: re-check API key and network; verify resolution matches configured value.
- Template misses: confirm resolution and assets in `Resources/<res>/...`.
- Script won’t start: ensure `manifest.json` is valid and the entry point exists.

## Development
- Build: `dotnet build`
- Run: `dotnet run --project ProjectMaelstrom`
- Core tests: `dotnet test ProjectMaelstrom/ProjectMaelstrom.sln -c Debug`
- Toolkit selftest: `dotnet run --project MaelstromToolkit/MaelstromToolkit.csproj -- selftest`

## Credits & Licenses
- Emgu CV (OpenCV bindings) for image processing and template matching (BSD).
- Tesseract OCR (Apache 2.0) for local text extraction.
- WindowsInput/InputSimulator (MIT) for keyboard input.
- Newtonsoft.Json (MIT) for JSON handling.
- System.Drawing / Win32 interop for window/input helpers.
- Community scripts/bots in `Scripts/Library` retain their original authorship; source URLs and authors should be listed in each `manifest.json` and surfaced in-app.

## TODO (single list)
- UI/UX: fix button text clipping/spacing across all forms; give nav buttons more width; surface script author/source in the main list; wire "Run Macro" entry in nav to the Macro Runner; explore an optional Steam/Nvidia-style in-game overlay for status/hotkeys.
- SmartPlay/Learn Mode: expose learn-mode profile (mixed/seek/avoid) and monster seek/avoid toggles; add health/mana/resource guards and auto-pause when Wizard101 loses focus; show SmartPlay queue length/status; keep capture/record behind dev when appropriate; spike "task learning" that watches player inputs and derives repeatable tasks/macros safely; leverage WizWiki data (cached/offline) to map mobs/zones for seek/avoid routing without live scraping.
- Pathing & resources: teach SmartPlay to learn spawn locations for reagents and wooden chests; pull/map data from Wiz101 Wiki (offline/cache) to build and verify travel routes for resource runs; integrate into pathing macros.
- Theme & assets: capture Wizard101 UI colors/fonts/assets from the local install; Wizard101-inspired theme switcher; automated reference screenshots; allow read-only access to game files/screenshots and wizard101.com for visual reference.
- Launcher integration: "Launch Wizard101" uses default paths (e.g., `C:\ProgramData\KingsIsle Entertainment\Wizard101\Wizard101.exe`) before prompting; detect launcher states (login/patch/play) and surface them in sync indicators; refine detection with launcher UI cues.
- Script library: embed the full library in packaged releases; default feed fallback in Project Manager and prompt for manual URL only when auto-fetch fails and an update is available; package bots/utilities as installable entries; finish attribution for remaining scripts (afk-wizard, gardening-bot, wiz-packet-map, wizAPI, Wizard101-Farming, Wizard101-Utilities, wizwad, nested GrubNinja).
- Project Manager/Installer: tidy status layout; version check before launching the main app; portable ZIP option; dev-only controls guarded by dev key; error logging on update/install failures; merge Script Loader/Project Manager views so add-ons are consistent.
- Diagnostics: onboard logging/health for SmartPlay and installer; design manager to capture UI screenshots for QA; avoid sensitive data in logs; keep password logging disabled.
- Major UI/UX overhaul: modernize the main trainer and installer with a cohesive theme (Wizard101-inspired + system-friendly), reorganize controls into clearer sections/menus (e.g., settings vs. scripting vs. travel), and share theme assets between app and installer for a unified look.
- Audit bots: review all bundled Wizard101 bots/utilities to see which we can outperform or which are obsolete; identify candidates to replace with native implementations and note attribution.
- Script cataloging: analyze, prioritize, and categorize all player-visible scripts (native vs external vs reference/deprecated) to surface only high-value options to players and streamline updates.
- Resource runners: design and implement resource-aware runs (energy/mana/potion checks) that auto-queue refills and avoid starting tasks when resources are too low.
- Simplify structure: avoid repetitive directories and simplify systems/projects where it benefits player experience and reduces clutter.
- Knowledge surfacing: aggregate player guides, monster behavior, and game mechanics (via cached sources like WizWiki or local notes) so SmartPlay can surface relevant info/context to the player in-app.
- Internal bridge: unify non-UI execution (script runner, SmartPlay, resource guards) behind a single integration layer so core functions can run seamlessly without extra UI wiring.
- Wiki data fetch helper: use `tools/wiki_fetch_template.ps1` to download target wiki pages to `Scripts/Library/WizWikiAPI-main/wiki_fetch_raw`; then convert to JSON (`wizwiki_*`) for the app to load (resources/NPCs/quests/zones/crafting). No live scraping at runtime.
- World assets: raw Wizard101 world pages/images saved under `ProjectMaelstrom/Scripts/Library/WizWikiAPI-main/worlds_raw/` (from desktop W101 folder). Convert these to `wizwiki_zones.json` + map images and use Settings → Refresh Wiki Cache to load.

## Safety & Fair Play
- Use responsibly. Respect game terms of service and other players.
- Run in windowed mode; keep an eye on automation and stop immediately if something looks wrong.
- A global stop/pause hotkey and simulation/dry-run mode are recommended next improvements.

## Project Layout
```
ProjectMaelstrom/
  ProjectMaelstrom.sln
  ProjectMaelstrom/           # WinForms app
    Main.cs                   # Main UI + bot launcher + script library panel
    Utilities/                # Logging, storage, sync, library services
    Modules/ImageRecognition/ # Template matching and OCR helpers
    Resources/<res>/...       # Templates per resolution
    Scripts/                  # Bundled scripts and Library for custom scripts
    tessdata/                 # Tesseract data
```




### MaelstromBot localhost/tunnel mode
- Default: single port (http://localhost:5000) for /webhooks and /bot endpoints.
- Optional: dual-port mode (pure localhost) via env/config:
  - MAELSTROM_PORT_MODE=dual
  - MAELSTROM_WEBHOOKS_PORT=9410 (tunnel ONLY this port)
  - MAELSTROM_ADMIN_PORT=9411 (local admin API + /bot/ui; do NOT tunnel)
- Webhook URLs (dual): http://127.0.0.1:9410/webhooks/github and /webhooks/openai; admin UI/API: http://127.0.0.1:9411/bot/ui and /bot/api.
- Tray can point to admin port (configurable base URL in tray Settings).


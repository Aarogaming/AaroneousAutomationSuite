# UiAuditRunner (Dev-only)

Purpose: Launch ProjectMaelstrom, capture UI screenshots, and build `ui_audit_pack.zip` for review. No clicks or input are sent; windows are captured if already open/visible.

## Prereqs
- Windows with UI access (not headless).
- .NET 9 SDK (or compatible with the TFM in `UiAuditRunner.csproj`).

## Build
```pwsh
dotnet build DevTools/UiAuditRunner/UiAuditRunner.csproj -c Debug
```

## Configure
- Copy `DevTools/UiAuditRunner/config.sample.json` to `config.json`.
- Edit:
  - `projectExePath`: full path to ProjectMaelstrom.exe (e.g., `ProjectMaelstrom\ProjectMaelstrom\bin\Debug\net9.0-windows10.0.22621.0\ProjectMaelstrom.exe`)
  - `dpiScales`: list of scales you will capture (set OS scale manually per run)
  - `mainWindowTitleHint`: substring of the main window title (e.g., `Maelstrom`)
  - `openScreens`: true to attempt opening Settings/Plugins/Manage Scripts/GitHub dialog via UIA
  - `timeoutSeconds`: wait time for windows/controls
  - `navigation`: name hints to locate buttons/tabs (Settings, Manage Scripts, Plugins, GitHub Install)
  - `screens`: window title substrings to find (Main/Settings/Manage Scripts/etc.)
  - `outputFolder`: e.g., `ui_audit_pack`
  - `zipOutput`: base zip name (tool will append DPI label)

## Run
```pwsh
dotnet run --project DevTools/UiAuditRunner/UiAuditRunner.csproj --config ./DevTools/UiAuditRunner/config.json
```

Notes:
- Set OS display scale manually to 100/125/150/175 before each pass (use DpiLabel in config for naming).
- UIA-only: uses Invoke/Selection patterns (no SendKeys/mouse).
- If a window/control is not found, it logs in README.txt and continues.
- Output: PNGs + README in `outputFolder`, zipped to `ui_audit_pack_{DpiLabel}.zip` (or first DPI if not set).

## Run all DPIs with prompts
Use the helper script (DPI still set manually):
```pwsh
powershell -ExecutionPolicy Bypass -File ./scripts/run_ui_audit_all.ps1
```
You will be prompted to set Windows display scale for each DPI (100/125/150/175); the script updates `dpiLabel` in config.json, runs UiAuditRunner, and prints paths to the generated zips.

## Safety
- No code in ProjectMaelstrom is modified or referenced by this tool.
- No input is sent; if a window is not found, it logs and continues.

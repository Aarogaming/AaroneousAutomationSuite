# Release Readiness (Aaroneous Automation Suite)

## 1) Overview
Aaroneous Automation Suite is policy-driven; live automation is governed by the `ALLOW_LIVE_AUTOMATION` flag. Default profile: Public. **Gold Freeze: ACTIVE**.

## 2) Build Commands
- Debug: `dotnet build ProjectMaelstrom/ProjectMaelstrom.sln -c Debug`
- Release: `dotnet build ProjectMaelstrom/ProjectMaelstrom.sln -c Release`

## 3) Portable Packaging
- Default portable build: `./scripts/build_portable.ps1`
- With sample plugins: `./scripts/build_portable.ps1 -IncludeSamples`
- Output: `artifacts/portable/`
- DevTools are excluded from portable builds by default.

## 4) Quality Gates (must-pass)
- UI regression:
  - Baseline refresh: `powershell -ExecutionPolicy Bypass -File ./scripts/ui_set_baseline.ps1`
  - Check: `powershell -ExecutionPolicy Bypass -File ./scripts/ui_check_regression.ps1` (default threshold 0.5%)
- UI spot-check: Developer Options → Minigames shows planned catalog entries when SampleMinigameCatalog is installed.
- Functional tests:
  - Run FunctionalTestRunner (ensure it passes; uses inline fixtures incl. corrupt manifest check).
- Secret preflight:
  - `powershell -ExecutionPolicy Bypass -File ./scripts/scan_for_secrets.ps1` (exit code 0 required)
- Known benign warnings: Tesseract "missing tessdata" messages may appear in DevTools self-capture; harmless. To silence, set `TESSDATA_PREFIX` to the tessdata folder or ignore during capture.

## 5) GitHub Secret Scanning
- If alerts exist: redact in repo (see SECURITY_NOTES.md), then close alerts as "Revoked" with a brief comment (e.g., third-party embed keys redacted; not used by app).

## 6) Release/Submission Checklist
- [ ] Debug build passes
- [ ] UI regression check passes (threshold acceptable)
- [ ] Functional tests pass
- [ ] Secret scan returns 0 findings
- [ ] Portable build (if needed) succeeds and excludes DevTools
- [ ] GitHub secret alerts closed or none outstanding
- [ ] Policy defaults recorded (e.g., current `ALLOW_LIVE_AUTOMATION` setting; Public profile)

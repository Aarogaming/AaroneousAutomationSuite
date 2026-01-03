# Co-op Workflow (Aaroneous Automation Suite)

## Final Phase Checklist
- UI polish locked: verify 150% / 175% captures via UiAuditSelfCapture.
- Regression lock: set baseline (`scripts/ui_set_baseline.ps1`) and run diff (`scripts/ui_check_regression.ps1`, threshold 0.5% default).
- Warning cleanup: zero compiler warnings before release (Debug/Release).
- Release readiness:
  - Portable build excludes DevTools and samples by default.
  - No secrets/tokens in repo or configs.
  - Document any known limits in PACKAGING.md / release notes.

## Fast Loop (one command)
- `./scripts/coop_loop.ps1 -Watch` (or without -Watch to prompt)  
  Steps: paste Codex output -> generates handoff (clipboard) -> paste into ChatGPT -> use `./scripts/handoff_to_codex.ps1` footer when prompting Codex.

## Evaluation + handoff
- See `docs/COOPERATIVE_EVALUATION.md` for rubric (professor review, CI/CodeX, safety/determinism).
- Handoff updates flow through HandoffTray/toolkit/scripts; keep `artifacts/handoff/**` outputs current.

## Preflight Secret Scan
- Run before push: `./scripts/scan_for_secrets.ps1`
  - Scans common extensions for ghp_/AIza/private keys.
  - Exit 1 if any hits; review/redact (vendor third-party assets if needed).

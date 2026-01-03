# Audit Trail (Aaroneous Automation Suite)

## Purpose
Provide a deterministic record of verification steps, policy boundaries, and capability status for audits.

## Current Gold Snapshot
- Gold freeze: ACTIVE (see GOLD_FREEZE.md)
- Commit: 0295195
- Policy defaults: Public profile; ALLOW_LIVE_AUTOMATION=false
- Portable build: DevTools excluded by default; samples optional

## Verification Artifacts
- Final verify: artifacts/submission/final_verify_report.txt
- Portable verify (optional): artifacts/final_verify_portable_report.txt
- UI diff: artifacts/submission/ui_diff_report.txt
- Functional tests: artifacts/submission/functional_test_runner.txt
- Secret scan: artifacts/submission/secret_scan.txt

## Capability Boundaries
- LiveIntegration: blocked by default (policy)
- OverlayWidgets, ReplayAnalyzers, MinigameCatalog: allowed in Public/Experimental (read-only)
- No live automation allowed in gold build

## Config Flags (defaults)
- ALLOW_LIVE_AUTOMATION=false
- EXECUTION_PROFILE=AcademicSimulation

## Audit Steps (suggested)
1) Verify policy file: execution_policy.conf matches defaults.
2) Run `scripts/final_verify.ps1` (or use existing report).
3) Confirm UI diff report is within threshold (0.5%).
4) Confirm FunctionalTestRunner PASS.
5) Confirm secret scan PASS.
6) Verify portable build is DevTools-free.

## Attestation Templates
- Compliance: "We attest all default policies remain enforced as documented; live automation settings were reviewed."
- Reproducibility: "We attest builds were produced from commit <hash> using `scripts/final_verify.ps1` and match recorded checksums."

## Updates
- 2025-12-31: Added continuity docs (ROADMAP, GOALS, COOPERATIVE_EVALUATION, POLICY_TXT_SPEC), prompt protocol in ASSISTANT_CONTEXT, and handoff continuity notes. Purpose: preserve no-swerving policy, live-means-live governance, and professor review continuity.
- 2025-12-31: Added aas.policy.txt default policy (TXT) to keep governance in a single editable file.

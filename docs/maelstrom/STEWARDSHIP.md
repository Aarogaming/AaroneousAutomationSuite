# Stewardship (Aaroneous Automation Suite)

## Role Responsibilities
- Preserve gold build immutability and policy boundaries (Public profile, ALLOW_LIVE_AUTOMATION=false).
- Guard archives, baselines, and verification artifacts; ensure reproducibility.
- Run verification gates before any release/tag actions; block scope or feature expansion.

## Succession Rules
- Stewardship is custodial only; no authority to expand scope.
- Successor must agree to policy boundaries and immutability before handoff.
- Handoff occurs from steward to steward (not via ad-hoc delegation).

## Acceptance Checklist
- Reviewed GOLD_FREEZE.md, AUDIT_TRAIL.md, MAINTENANCE.md, SECURITY_NOTES.md.
- Ran `scripts/final_verify.ps1` (or validated the latest reports).
- Verified policy defaults and portable build exclusions are intact.
- Acknowledged no live automation and no scope expansion.

## Handoff Protocol
- Exchange current commit hash, verification reports, and checksums.
- Confirm archives (portable, baselines, reports) are present and unchanged.
- Record handoff in the stewardship decision log.

## Contact Registry (offline)
- Maintain steward contact list and escalation paths offline (not stored in repo).

## Inactivity / Replacement
- Inactivity timeout: if steward is unreachable beyond agreed window, initiate emergency replacement.
- Emergency replacement requires re-running verification gates and re-acknowledging immutability.

## Decision Log Template
- Date / Steward
- Context / Decision
- Impact (none/minimal; no scope change allowed)
- Artifacts referenced (reports, hashes)
- Notes

## Scope Guard
- Stewardship does not grant authority to change scope, enable live automation, or alter gold artifacts.

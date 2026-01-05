# MaelstromToolkit Phase 1 Spec Lock

Scope
- Tooling/docs only for MaelstromToolkit (net8.0). Do not touch Aaroneous Automation Suite runtime/policy/UI/tests. No baseline refresh. No gold retagging.

Current reality (from recon)
- CLI commands: init; policy init; tags init; stewardship init; ux init (--framework); ci add (--provider/--profile); handoff; selftest. Flags: --out, --force, --dry-run, --verbose, --help, --version.
- Manifest: MaelstromToolkit/Templates/manifest.json (schemaVersion=1) listing name+folder only; no required_vars/output paths.
- Schema version: Templates/schema_version.txt = "1".
- Placeholder syntax observed: {{FRAMEWORK}} in Templates/UX/UX_STYLE_GUIDE.md; others have no placeholders.
- Resolution: templates resolved by folder inference (templateFolderFor) and written to --out/<templateName>; manifest not authoritative for paths/vars yet.

Phase 1 targets (future work)
- Exit codes: 0 success; 1 args/usage; 2 validation; 3 IO; 4 selftest.
- Strict vars: enforce required_vars; support --vars <json or path>; support repeatable --set key=value; precedence defaults < --vars < --set; fail before writing if missing/unresolved vars.
- Plan/dry-run: deterministic CREATE/OVERWRITE/SKIP with reasons; stable ordering (Ordinal); flags --fail-on-existing; optional --plan-json for machine-readable plan.
- Per-command help: short description, 2�3 examples with --out, files written (manifest-driven when available), stop conditions.

Determinism requirements
- Stable ordering for plans and missing-var reporting (StringComparer.Ordinal).
- UTF-8 (no BOM) + LF line endings for generated text.
- Writes only under --out; no overwrites unless --force (or fail-on-existing blocks).

Slices (suggested order)
1) Standardize exit codes across CLI.
2) Strict template vars (--vars/--set, required_vars enforcement).
3) Plan/dry-run output (CREATE/OVERWRITE/SKIP, fail-on-existing, optional plan JSON).
4) Per-command help/examples sourced from manifest metadata.

Non-goals
- No changes to Maelstrom runtime/policy/UI/tests.
- No baseline refresh, no gold retagging.
- No behavioral changes to toolkit in this doc slice (spec only).

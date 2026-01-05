# Cooperative Evaluation & Review

## Rubric (professor review)
- Policy/ethics: aas.policy.txt valid, LIVE means LIVE, no fallback; ethics/privacy keys respected.
- Safety: deny-unknown-capabilities honored; invalid edits rejected with LKG; no secrets in repo.
- Determinism: diagnostics stable and sorted; outputs reproducible.
- Scope discipline: tooling/docs only; no ProjectMaelstrom runtime changes without approval.

## Rubric (CodeX/CI)
- Build/test/tooling: dotnet build/test pass; toolkit `policy validate` passes on aas.policy.txt.
- Docs: ROADMAP, GOALS, COOPERATIVE_EVALUATION, POLICY_TXT_SPEC, handoff docs updated when behavior changes.
- Audit: AUDIT_TRAIL.md updated for milestones.
- Handoff: copyable prompt for ChatGPT 5.2 Pro provided in outputs.

## Policy apply history artifacts
- ACCEPTED policies (validate/watch) write under `--out/policy/history/<hash>/`:
  - `policy.txt`, `policy.sha256`
  - `effective.txt`
  - `eval.md`, `eval.json` (changed fields, risk level, notes)

## PR checklist
- [ ] Scope limited to tooling/docs (or approved runtime scope).
- [ ] aas.policy.txt validated; diagnostics written under `--out/system`.
- [ ] Tests/build/CI steps run as applicable.
- [ ] Docs updated (roadmap/goals/coop-eval/policy spec/handoff).
- [ ] AUDIT_TRAIL.md entry added.
- [ ] COPYABLE HANDOFF PROMPT included in summary.

## Professor review checklist
- [ ] LIVE means LIVE rule preserved (no silent fallback).
- [ ] Profiles defined and valid (requireAllProfilesValid).
- [ ] LKG behavior confirmed: invalid edits do not brick; fallback noted.
- [ ] AI provider settings align with policy (provider/apiKeyEnv/model).
- [ ] Handoff packet current and copyable.

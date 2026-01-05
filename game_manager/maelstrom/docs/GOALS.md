# Aaroneous Automation Suite — Goals & Quality Gates

## Quality gates
- Deterministic outputs (templates, diagnostics, hashes); avoid nondeterminism.
- Non-bricking policy edits: invalid aas.policy.txt rejected with LKG fallback.
- Safe writes: tooling writes only under `--out`; no git-tracked artifacts.
- No new production dependencies without approval.
- Tests/CI: build + tests + toolkit policy validate must pass.

## Platform goals
- Provider-agnostic AI: scaffold supports openai/http/none with env-var key references (no secrets in repo).
- Packs catalog: core stays domain-agnostic; domains live in packs (Wizard101 later as a pack).
- Connectors: desktop/input/screen/audio/network as pluggable capabilities, policy-gated.
- Handoff continuity: handoff docs and artifacts kept current for cross-agent workflows.

## Non-negotiables
- LIVE means LIVE: no global downgrade; if capabilities missing, mark live as DEGRADED/BLOCKED with reasons.
- Keep ProjectMaelstrom runtime untouched unless explicitly approved.
- No baseline refresh or gold retagging in this phase.

# Aaroneous Automation Suite & DevTools Roadmap

> **⚠️ DEPRECATED**: This roadmap has been consolidated into [AAS MASTER_ROADMAP.md](../../../docs/MASTER_ROADMAP.md).  
> See Phase 3.1 for game automation details.

---

## Purpose
AI Automation Suite first (desktop/live), prepped for Home Hub / Home OS later. DevTools provide local-first server + tray + toolkit for policy enforcement, handoff, and automation scaffolds.

## Guiding principles
- **LIVE means LIVE:** if a live profile is active, OperatingMode stays LIVE; missing capabilities result in DEGRADE/BLOCK, not fallback.
- **Deterministic:** templates/outputs reproducible; avoid nondeterminism.
- **Safe policy edits:** aas.policy.txt is professor-editable; invalid edits are rejected with LKG fallback.
- **No new prod deps / safe writes:** tooling only, writes under `--out`.

## Milestones
1) Policy TXT (aas.policy.txt) + validation/LKG + docs.
2) Packs model (domain packs; Wizard101 becomes a pack later).
3) AI provider wiring (provider-pluggable: openai/http/none scaffold).
4) Live connectors (desktop/input/screen) with capability gating.
5) Service mode (Home Hub / Home OS readiness).

## Current focus
- Toolkit commands for policy validate/effective/watch; ensure LKG and deterministic diagnostics.
- Document continuity: roadmap, goals, cooperative evaluation, policy spec, handoff protocol.
- Keep runtime frozen; no baseline refresh.

## Later
- Expand catalog to additional packs and connectors.
- Wire actual AI providers and connectors once policy/ethics approved.

# HandoffTray (Tray + Watcher)

- Windows-only tray helper (net9.0 WinForms). Run from repo root.
- Modes: Off (default), Watch To-Codex, Watch From-Codex, Both.
- Actions: Copy latest HANDOFF_TO_CODEX, run handoff import (toolkit CLI), send latest prompt via API (toggle), open reports folder.
- API send: default OFF, requires env `OPENAI_API_KEY`, per-send confirmation, redacts obvious secrets, writes responses to `artifacts/handoff/reports/OPENAI_RESPONSE_*.md`.
- Artifacts/logs: `artifacts/handoff/**` (ignored).
- Safety: no auto-posting; toggle + confirmation required. No secrets stored.
- CLI dependency: `dotnet` available; runs `dotnet run --project MaelstromToolkit/MaelstromToolkit.csproj -- handoff import --out artifacts/handoff/reports`.
- Server status check: tray menu → “Check server status” (expects local API at `http://127.0.0.1:9411/api/status`).

## Continuity Protocol
- All chats/agents must use copyable prompts; CodeX outputs end with a “COPYABLE PROMPT FOR CHATGPT 5.2 PRO”.
- Keep continuity docs current: `docs/ROADMAP.md`, `docs/GOALS.md`, `docs/COOPERATIVE_EVALUATION.md`, `docs/POLICY_TXT_SPEC.md`.
- Handoff artifacts live under `artifacts/handoff/**` (ignored by git).
- Relevant scripts: `scripts/handoff_from_codex.ps1`, `scripts/handoff_to_codex.ps1`, `scripts/coop_loop.ps1`.
- Latest commit/branch in generated prompts: prefers `GITHUB_SHA`, otherwise `git rev-parse`; dirty flag via `git status --porcelain`.

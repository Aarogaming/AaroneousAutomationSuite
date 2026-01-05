## Assistant Context — Aaroneous Automation Suite

### Architecture (high level)
- **ProjectMaelstrom**: WinForms automation app with policy-driven executors and profiles.
- **MaelstromBot.Server**: Webhook-driven job queue + OpenAI background pipeline. Admin APIs under `/bot/api`, dashboard at `/bot/ui`, health at `/healthz`, webhooks at `/webhooks/github` and `/webhooks/openai`.
- **HandoffTray**: WinForms tray client that polls `/bot/api`, shows notifications, toggles automations, and can cancel latest awaiting job. Stores only the server-issued token (DPAPI CurrentUser).
- **MaelstromToolkit**: Dev tooling (templating/handoff/selftest); not part of runtime app.

### Default safety posture
- `ALLOW_LIVE_AUTOMATION` flag governs live automation; set per profile/environment.
- OpenAI API key never leaves the server; tray uses only the server-issued token.
- Webhooks must be signature-verified (GitHub HMAC, OpenAI Standard Webhooks).

### Endpoint map
- `/healthz` – basic liveness.
- `/bot/api/*` – authenticated (Bearer token). Examples: `/bot/api/status`, `/bot/api/jobs`, `/bot/api/automations`.
- `/bot/ui` – local dashboard (enter token in the page to call `/bot/api`).
- `/webhooks/github` – GitHub push webhook (expects X-Hub-Signature-256).
- `/webhooks/openai` – OpenAI Standard Webhooks (response.completed).

### Dual-port mode (optional)
- Webhook port (e.g., `9410`): only `/webhooks/*` (plus `/webhooks/healthz`). Wrong paths should 404.
- Admin/UI port (e.g., `9411`): only `/bot/*` (and `/healthz`). Wrong paths should 404.
- Single-port mode remains default; dual mode enabled via env/config (`MAELSTROM_PORT_MODE=dual`).

### Required environment variables
- `OPENAI_API_KEY` – server-side OpenAI access (background Responses API).
- `OPENAI_WEBHOOK_SECRET` – Standard Webhooks signing secret (OpenAI).
- `GITHUB_WEBHOOK_SECRET` – HMAC secret for GitHub webhooks.
- Optional:
  - `MAELSTROM_PORT_MODE` (`single`|`dual`), `MAELSTROM_WEBHOOKS_PORT`, `MAELSTROM_ADMIN_PORT`.
  - `OPENAI_MODEL` (default `gpt-5.2`).

### Job lifecycle (server)
`queued` → `running` → `awaiting_openai` → `completed_pending_fetch` → `completed` (or `failed` / `cancel_requested`).  
Visible via `/bot/api/jobs` and `/bot/api/status`; `/bot/ui` renders summaries.

### Known gotchas
- Missing .NET runtime/ASP.NET shared runtime → run `dotnet --list-runtimes` and install matching version.
- SQLite schema/init failures → reset local DB (artifacts/bot/db/maelstrombot.db) and rerun `--init-admin-key`.
- Dual-port mode 401/404 → check port vs path and Bearer token.
- Port conflicts → choose alternate ports via env vars.

## Prompt Protocol
- All assistant outputs to user are copyable prompts to CodeX Agent.
- CodeX must output a copyable prompt intended for ChatGPT 5.2 Pro.
- HandoffTray system + continuity docs are the source of truth (see ROADMAP/GOALS/COOPERATIVE_EVALUATION/POLICY_TXT_SPEC).

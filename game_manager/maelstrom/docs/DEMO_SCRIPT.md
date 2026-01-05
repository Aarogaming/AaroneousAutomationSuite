# Demo Script — Aaroneous Automation Suite & DevTools (2–5 minutes)

## Setup (one-time)
- Ensure env vars are set:
  - OPENAI_API_KEY
  - OPENAI_WEBHOOK_SECRET
  - GITHUB_WEBHOOK_SECRET (optional)
- Optional dual-port:
  - MAELSTROM_PORT_MODE=dual
  - MAELSTROM_WEBHOOKS_PORT=9410
  - MAELSTROM_ADMIN_PORT=9411

## 1) Build
dotnet build ProjectMaelstrom/ProjectMaelstrom.sln -c Debug

## 2) Initialize admin key (prints token)
dotnet run --project MaelstromBot.Server -- --init-admin-key

## 3) Start server
dotnet run --project MaelstromBot.Server

## 4) Verify health and auth (curl examples)
```
# single-port example:
curl.exe -i http://localhost:5000/healthz
curl.exe -i -H "Authorization: Bearer <TOKEN>" http://localhost:5000/bot/api/status
```

## 5) Open dashboard
http://localhost:5000/bot/ui

## 6) Start tray
- Set base URL to server admin base
- Paste token
- Confirm:
  - tooltip counts update
  - notification on completion/failure
  - automation toggles change state
  - cancel latest awaiting job works

## Optional: Webhooks
- Tunnel to /webhooks/github and /webhooks/openai
- Trigger a job
- Observe lifecycle: queued → awaiting_openai → completed_pending_fetch → completed
- Confirm result_text appears in /bot/api/jobs and /bot/ui


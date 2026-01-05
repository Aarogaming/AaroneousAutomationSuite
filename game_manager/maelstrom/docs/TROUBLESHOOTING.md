# Troubleshooting — Aaroneous Automation Suite & DevTools

## 1) Server won't start: missing runtime
Symptom:
- App fails with a message about missing `Microsoft.AspNetCore.App` for the target runtime.

Fix:
- Install the required ASP.NET Core Runtime for the targeted .NET version.
- Verify installed runtimes:
  - `dotnet --list-runtimes`

Notes:
- If you have a newer major runtime installed, .NET may not roll-forward across major versions unless configured.

## 2) `--init-admin-key` fails with SQLite schema syntax error
Symptom:
- SQLite error near `CREATE TABLE`, `incomplete input`, or similar during schema init.

Most common causes:
- Multiple SQL statements executed in one string without proper `;` separators.
- A string literal bug injecting stray characters (e.g., an accidental leading quote).
- Non-SQLite tokens copied from another SQL dialect.

Fix approach:
- Execute schema statements **one at a time** (array of statements) so failures isolate cleanly.
- Ensure every statement ends with `;`.
- Delete the local dev DB file to reset state (search for `*.db` if path unknown).

## 3) `/bot/api/*` returns 401
Symptom:
- You hit `/bot/api/status` and get 401.

Fix:
- Ensure header:
  - `Authorization: Bearer <TOKEN>`
- Ensure you’re hitting the correct base URL/port (especially in dual-port mode).

## 4) Dual-port mode returns 404
Expected behavior in dual-port mode:
- `/webhooks/*` only on webhook port
- `/bot/*` only on admin port
So 404 on the wrong port is expected.

Fix:
- Verify env vars:
  - `MAELSTROM_PORT_MODE=dual`
  - `MAELSTROM_WEBHOOKS_PORT=9410`
  - `MAELSTROM_ADMIN_PORT=9411`
- Re-check which URL you’re calling.

## 5) Port already in use
Symptom:
- Startup fails binding to a port.

Fix:
- Stop the other process or change configured ports.

## 6) CI warning NETSDK1206 (RID warning)
Symptom:
- Build shows NETSDK1206 about version-specific RIDs.

Impact:
- Typically non-fatal; fix later by updating package references or runtime identifier configuration.


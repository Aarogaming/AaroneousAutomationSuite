# IPC Conventions (Integration Hub)

This hub standardizes cross-project interaction using **file-based IPC** with **JSON Schema validation**.

## Canonical channels
- `handoff` — work packets/envelopes between components
- `commands` — player/game commands (input batches)
- `snapshots` — published game state snapshots

## Directory layout
All IPC lives under:
- `AaroneousAutomationSuite/artifacts/ipc/<channel>/`

Each channel has 3 folders:
- `inbox/` — producers drop JSON files here (write-then-rename)
- `outbox/` — validated/accepted messages ready for consumption
- `deadletter/` — rejected messages + a `.error.txt` reason file

Example:
- `artifacts/ipc/commands/inbox/20260113T010203Z_command.json`

## File creation rules (avoid races)
Producers MUST:
1. Write to `*.tmp`
2. Rename to `*.json` atomically

Consumers MUST:
- Move (rename) files out of `outbox/` before processing.

## Outbox claim convention (consumer safety)
To prevent double-processing when multiple consumers watch the same outbox:

1. Consumers MUST claim by atomic move:
   - `outbox/<file>.json` -> `processing/<consumerId>/<file>.json`
2. If the move fails, another consumer already claimed it.
3. After processing:
   - success: delete the claimed file, or move to an app-specific archive
   - failure: move to `deadletter/` + write `<file>.error.txt`

Directory layout per channel:
- `outbox/`
- `processing/<consumerId>/`
- `deadletter/`
- `archive/<consumerId>/` (for processed messages)

## Consumer loop template
Use `eng/ipc-consumer-loop.ps1` to build workers that claim and process messages:

### Continuous processing:
```powershell
.\eng/ipc-consumer-loop.ps1 -Channel commands -ConsumerId myWorker
```

### One-shot processing:
```powershell
.\eng/ipc-consumer-loop.ps1 -Channel commands -ConsumerId myWorker -Once -MaxPerLoop 5
```

### Custom processing logic:
```powershell
$process = {
  param($msg)
  # Your logic here, e.g., send to API, update DB
  if ($msg.commands.Count -gt 0) { throw "Simulated error" }
}
.\eng/ipc-consumer-loop.ps1 -Channel commands -ConsumerId myWorker -Once -ProcessScript $process
```

Success moves to `archive/<consumerId>/`, failure to `deadletter/` with error file.

## Validation
- Every JSON file should include `schemaName` and `schemaVersion`.
- Run contract validation for schemas/examples:
  - `eng/validate-contracts.ps1`
- Use the IPC router for inbox validation/routing:
  - `eng/ipc-router.ps1` (routes inbox -> outbox/deadletter)

### IPC router usage
Validate and route continuously:
```powershell
powershell -ExecutionPolicy Bypass -File .\eng/ipc-router.ps1
```

Process once (useful for CI or debugging):
```powershell
powershell -ExecutionPolicy Bypass -File .\eng/ipc-router.ps1 -Once
```

Channel-specific:
```powershell
powershell -ExecutionPolicy Bypass -File .\eng/ipc-router.ps1 -Channel commands -Once
```

### Schema enforcement
When `ProjectMaelstrom/tools/MaelstromToolkit` is available, the router validates:
- `commands/*` against `CommandBatch 1.0.0`
- `snapshots/*` against `GameStateSnapshot 1.0.0`
- `handoff/*` against `HandoffEnvelope 1.0.0` + payload validation

If the toolkit is not present, the router falls back to light validation (JSON parse + `schemaName`/`schemaVersion`).

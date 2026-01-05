# POLICY TXT SPEC (aas.policy.txt)

## Format
- Plain text, INI-like.
- Comments start with `#` or `;`.
- Sections use `[section]`; keys use `key = value`.
- Unknown keys: allowed if `denyUnknownKeys=false`; otherwise errors.

## Required sections/keys
[global]
- schemaVersion = 1
- activeProfile = <profile name>
- onInvalidConfig = keepLastKnownGood
- requireAllProfilesValid = true
- denyUnknownCapabilities = true
- denyUnknownKeys = false
- liveMeansLive = true
- safeWrites = outOnly

[ethics]
- purpose = educational_research
- requireConsentForEnvironmentControl = true
- prohibit = comma-separated prohibitions
- privacy.noSecretsInLogs = true
- privacy.storeScreenshots = false
- privacy.storeAudio = false

[profile <name>] (required: catalog, simulation, live_advisory, live_pilot)
- mode = catalog|simulation|live
- autonomy = advisory|pilot|full (required for live profiles)

[ai]
- enabled = true|false
- provider = openai|http|none
- apiKeyEnv = <ENV VAR> (required when provider=openai)
- model = gpt-5.2-pro (example)
- temperature = 0
- allowSendScreenshotsToModel = false
- allowSendAudioToModel = false
- endpoint = <url> (optional, recommended when provider=http)
- allowedTools = (comma-separated; optional)
- deniedTools = (comma-separated; optional)
- store = false (optional; OpenAI “store”)
- reasoningEffort = none|medium|high|xhigh (optional)
- timeoutSeconds = 1..600 (optional; default 60)
- maxOutputTokens = 1..16384 (optional; default 1024)
- userTag = optional string (OpenAI “user” field)

## Validation rules
- schemaVersion must be 1.
- requireAllProfilesValid=true: missing/invalid required profiles cause errors.
- Unknown capabilities denied when denyUnknownCapabilities=true.
- Unknown keys error when denyUnknownKeys=true; warn otherwise.
- AI provider must be openai|http|none; apiKeyEnv required for openai.
- If provider=http, endpoint required.
- reasoningEffort must be one of none|medium|high|xhigh; temperature only supported when reasoningEffort=none (warning otherwise).
- timeoutSeconds/maxOutputTokens must be within bounds.
- LIVE means LIVE: if active profile mode=live, OperatingMode stays LIVE; blocked/degraded is reported, no fallback.

## LKG and non-bricking edits
- Invalid edits are rejected; diagnostics are deterministic and sorted.
- Last Known Good snapshot written to `--out/system/policy.lkg.txt` and hash to `--out/system/policy.lkg.sha256`.
- Rejected diagnostics written to `--out/system/policy.rejected.txt`.
- Tooling never overwrites aas.policy.txt automatically.

## Toolkit command (validate)
- Run: `dotnet run --project MaelstromToolkit/MaelstromToolkit.csproj -- aas policy validate --file ./aas.policy.txt --out ./--out`
- Writes under `--out/system/`:
  - `policy.validate.txt` (status, hash, activeProfile, OperatingMode, LiveStatus, diagnostics)
  - If valid: `policy.lkg.txt`, `policy.lkg.sha256`
  - If invalid: `policy.rejected.txt`
- `--out` path must contain `--out` segment; no writes otherwise.

## Toolkit command (effective with fallback)
- Run: `dotnet run --project MaelstromToolkit/MaelstromToolkit.csproj -- aas policy effective --file ./aas.policy.txt --out ./--out [--format text|json]`
- Resolution order: FILE → LKG (`--out/system/policy.lkg.txt`) → built-in DEFAULT (tooling safe defaults).
- Output always written under `--out/system/`:
  - `policy.effective.txt`
  - `policy.effective.json` (when `--format json`)
- Summaries include: source, hash, activeProfile, profileMode, OperatingMode, LiveStatus, reasons, AI summary, ethics summary, diagnostics, and top rejection codes for FILE/LKG if fallbacks were used.
- Invalid edits never brick: FILE errors are recorded, but LKG or DEFAULT keep the tool running.

## Toolkit command (watch / hot reload)
- Run: `dotnet run --project MaelstromToolkit/MaelstromToolkit.csproj -- aas policy watch --file ./aas.policy.txt --out ./--out`
- Behavior:
  - Debounced file watcher reads policy safely (retry on IO locks).
  - VALID edits: ACCEPTED, writes LKG (`policy.lkg.txt/.sha256`) and `policy.watch.last.txt`.
  - INVALID edits: REJECTED, keeps previous snapshot, writes `policy.rejected.txt`.
  - LIVE means LIVE preserved; no global fallback.
- Outputs under `--out/system/`.

## Policy apply history
- ACCEPTED policies (validate or watch) also write under `--out/policy/history/<hash>/`:
  - `policy.txt`, `policy.sha256`
  - `effective.txt`
  - `eval.md`, `eval.json` (changed fields, risk level, notes)

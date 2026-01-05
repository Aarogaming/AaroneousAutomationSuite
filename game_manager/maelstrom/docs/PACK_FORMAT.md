# PACK FORMAT

## pack.json
- Required fields: id, name, version, scenarios (array).
- Optional: description.
- Each scenario entry:
  - id (required)
  - name (required)
  - description (optional)
  - entry (required, relative path to scenario file)

## Scenario file (JSON)
- Must be valid JSON.
- Must contain `id` matching manifest scenario id.
- Suggested fields: summary, steps (array of strings).

## Validation rules
- pack.json must exist in each pack directory.
- id/name/version required; at least one scenario.
- Scenario entry file must exist and have matching id.
- Diagnostics are deterministic and sorted.

## Toolkit commands
- List: `dotnet run --project MaelstromToolkit -- aas packs list --root ./packs --out ./--out`
  - Writes `--out/packs/list.txt`
- Validate: `dotnet run --project MaelstromToolkit -- aas packs validate --root ./packs --out ./--out`
  - Writes `--out/packs/validate.txt`; exits non-zero on errors

# UiAuditDiff (DevTool)

Console helper to compare UiAuditSelfCapture outputs against a stored baseline for quick UI regression checks.

## Baseline
```pwsh
./scripts/ui_set_baseline.ps1
```
Creates `ui_baseline/` with fresh captures (100/125/150/175) plus `ui_audit_pack.zip`.

## Regression check
```pwsh
./scripts/ui_check_regression.ps1            # default threshold 0.5%
./scripts/ui_check_regression.ps1 -Threshold 0.25  # tighter threshold
```
Generates `ui_current/`, runs UiAuditDiff, and writes a report to `artifacts/ui_diff_report.txt`. Exit code 1 signals regression (missing baseline files or diffs above threshold).

## UiAuditDiff CLI
```
dotnet run --project DevTools/UiAuditDiff/UiAuditDiff.csproj -- --baseline ui_baseline --current ui_current --threshold 0.5 --report artifacts/ui_diff_report.txt
```
Args:
- `--baseline <path>` (required)
- `--current <path>` (required)
- `--threshold <float>` (optional, default 0.5)
- `--report <path>` (optional; if provided, writes report there)

Diff logic:
- Compares PNGs by filename.
- Reports Missing (in baseline, absent in current), New, and Changed (pixel diff % and mean channel delta).
- Dimension mismatch = 100% diff.
- Exit codes: 0 pass; 1 fail (missing baseline files or any diff above threshold or missing baseline folder).*** End Patch

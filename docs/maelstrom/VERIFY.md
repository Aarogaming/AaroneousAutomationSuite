# Verification Guide (Aaroneous Automation Suite)

## Checksums
- Portable: `artifacts/submission/checksums_portable.txt`
- Submission artifacts: `artifacts/submission/checksums_submission.txt`
- Verify on Windows PowerShell:
  ```pwsh
  Get-ChildItem artifacts/portable -Recurse | Get-FileHash -Algorithm SHA256
  Get-ChildItem artifacts/submission -File | Get-FileHash -Algorithm SHA256
  ```
  Compare against the stored checksum files above.

## How to Run
1) Extract `artifacts/portable/`.
2) Note: `execution_policy.conf` now writes `ALLOW_LIVE_AUTOMATION=true` by default (enforcement relaxed); profile = Public unless changed.
3) Run `ProjectMaelstrom.exe`.
4) DevTools are excluded; samples included only if previously built with `-IncludeSamples`.

## Reports
- Full gate run: `artifacts/submission/final_verify_report.txt`
- UI regression: `artifacts/submission/ui_diff_report.txt`
- Functional tests: `artifacts/submission/functional_test_runner.txt`
- Secret scan: `artifacts/submission/secret_scan.txt`
- Checksums: see above

## Policy Boundary
- Live automation currently allowed by default (`ALLOW_LIVE_AUTOMATION=true`); set the flag to false to disable live runs when needed.
- Portable build honors the same defaults.
- Details: see POLICY_BOUNDARY.md.

# Checksum Verification (Portable Build)

- Compute checksums for `artifacts/portable` before distribution.
- Recommended: SHA256 over the full folder (sorted) or on the produced ZIP if you package it.
- Example (PowerShell):
  ```pwsh
  Get-ChildItem artifacts/portable -Recurse | Get-FileHash -Algorithm SHA256
  ```
- Keep checksum records with release notes for reproducibility.

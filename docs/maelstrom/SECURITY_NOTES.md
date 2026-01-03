# Security Notes

- Third-party archived web assets (YouTube/Google embed files under `ProjectMaelstrom/Scripts/Library/WizWikiAPI-main/worlds_raw/`) contained Google embed keys.
- These keys are not used by Aaroneous Automation Suite and have been redacted (`REDACTED_GOOGLE_API_KEY`) to satisfy secret scanning.
- No application secrets or runtime credentials are stored in this repository.

## Maintenance Mode
- Gold freeze is active; default profile is Public and `ALLOW_LIVE_AUTOMATION=false`.
- Before merging to release branches, run `scripts/scan_for_secrets.ps1` and `scripts/final_verify.ps1`.

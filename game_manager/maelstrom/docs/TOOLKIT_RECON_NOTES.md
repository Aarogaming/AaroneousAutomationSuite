# MaelstromToolkit Recon Notes

## Current CLI surface
- Commands: init; policy init; tags init; stewardship init; ux init (--framework <value>); ci add (--provider <value> --profile <value>); handoff; selftest.
- Global flags parsed: --out, --force, --dry-run, --verbose, --help, --version. No per-command help yet; help is a single usage block.
- Current flow: requires --out for write commands; prints header "MaelstromToolkit <version> | command=..." before execution.

## Manifest and schema
- Manifest path: MaelstromToolkit/Templates/manifest.json
- Current shape (schemaVersion=1):
  ```json
  {
    "schemaVersion": 1,
    "templates": [
      { "name": "POLICY_BOUNDARY.md", "folder": "Policy" },
      { "name": "policy.config.sample", "folder": "Policy" },
      { "name": "TAG_POLICY.md", "folder": "Tags" },
      { "name": "STEWARDSHIP_CHECKLIST.md", "folder": "Stewardship" },
      { "name": "FEEDBACK_LOG.md", "folder": "Stewardship" },
      { "name": "UX_MAINTENANCE.md", "folder": "UX" },
      { "name": "UX_STYLE_GUIDE.md", "folder": "UX" },
      { "name": "UX_CHANGELOG.md", "folder": "UX" },
      { "name": "UX_TOKENS.md", "folder": "UX" },
      { "name": "github_tools-only_workflow.yml", "folder": "CI" },
      { "name": "README.md", "folder": "Handoff" }
    ]
  }
  ```
- Schema version file: MaelstromToolkit/Templates/schema_version.txt with value "1".
- Manifest currently lacks required_vars/optional_vars/output paths; code derives folder from template name via templateFolderFor.

## Placeholder syntax in templates
- Observed placeholder: `{{FRAMEWORK}}` in Templates/UX/UX_STYLE_GUIDE.md.
- Other templates (UX_MAINTENANCE.md, TAG_POLICY.md, POLICY_BOUNDARY.md, CI workflow) contain no placeholders.

## Template resolution (as implemented)
- Source path: Path.Combine(AppContext.BaseDirectory, "Templates", templateFolderFor(name), name), where templateFolderFor infers folder based on filename substrings/extension.
- Output path: `<out>/<templateName>` (not manifest-driven); overwrite only if --force.

## Safety mechanisms
- --out enforcement in Program.Main: RequiresOut + ValidateOut; blocks missing --out, filesystem root, and symlinked out dir; verbose logs resolved path.
- Atomic writes: WriteFile writes UTF-8 (no BOM) to `<dest>.tmp`, deletes on dry-run, otherwise File.Move overwrite; dry-run logs "would create/overwrite".

## Selftest
- Invocation: `dotnet run --project MaelstromToolkit/MaelstromToolkit.csproj -- selftest`.
- Checks: presence of schema_version.txt and manifest.json; verifies hardcoded template list exists; copies templates to a temp dir (with framework "winforms" where applicable); deletes temp dir; prints SELFTEST PASS/FAIL; returns 0 on pass, 1 on missing template/schema/manifest.

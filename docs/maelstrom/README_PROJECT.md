# Wizard101 Smart Trainer (Open-Source, Educational)

**Purpose:** Plan a smart-play trainer that uses public data and user-consented captures to assist with quest support, vision, and automation research. No live server interaction or TOS violations.

**MVP focus:** vision/OCR for UI state, safe input guardrails, offline learning from recordings, modular script manager, packaging for Windows.

## Legal & Ethics
- Educational/experimental only; open source; no commercial use implied.
- Use only public web data under respective licenses or user-provided, consented captures.
- Do **not** read/modify game memory, network traffic, or assets; do **not** automate against live servers without permission.
- Add attribution for third-party scripts and data sources (see About dialog).

## Files produced in this planning pass
- project_integration_plan.json
- repo_analysis_report.json (heuristic metadata)
- wizard101_data_sources.json
- seed_dataset_manifest.json (metadata only)

## Success metrics (early)
- 90%+ OCR accuracy on 1280x720 UI HUD elements using template+OCR blend.
- Stable input bridge with focus guard; zero unintended clicks outside game window.
- Script manager can install/run packaged bots with provenance and credits.
- Portable + installer builds verified on Windows 10/11.

## Immediate tasks (next 2 weeks)
- Wire SmartPlay dev mode: structured logging, self-checks, no password logging.
- Expand template library and OCR whitelist for common HUD elements (mana, health, energy).
- Build lightweight dashboard for diagnostics (PySimpleGUI/DearPyGui prototype).
- Finish Project Manager UX for updates, portable builds, and script catalog with credits.
- Draft contributor guidelines on safe data sourcing and attribution.

## Contact & permissions
- Confirm user consent for any shared captures; request explicit permission for third-party media when needed.

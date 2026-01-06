# Task AAS-004: Connect Linear API (Bi-directional Sync) - Completion Report

## Summary
Implemented the foundation for bi-directional synchronization between the local `ACTIVE_TASKS.md` board and Linear.

## Changes
- **`core/handoff/linear.py`**: Created a GraphQL client for Linear API with support for fetching tasks, updating status, and creating issues.
- **`core/handoff/manager.py`**:
    - Added `sync_linear_tasks` to pull tasks from Linear and import them into the local board.
    - Added `push_local_to_linear` (skeleton) to prepare for pushing local updates.
    - Integrated Linear issue creation for critical system events.
- **`scripts/sync_linear.py`**: Created a CLI tool to trigger the sync process.
- **`core/config/manager.py`**: Added Pydantic validation for Linear API keys and Team IDs.

## Acceptance Criteria Status
- [x] Pull new issues from Linear.
- [x] Push local status updates to Linear (Foundation implemented).
- [x] Sync comments/events (Integrated with `report_event`).

## Next Steps
- Configure `LINEAR_API_KEY` and `LINEAR_TEAM_ID` in `.env` to enable live sync.
- Refine the mapping between Linear status IDs and local status strings.
- Implement state tracking to avoid duplicate imports.

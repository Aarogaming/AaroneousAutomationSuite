# Handoff Service Contract v1.0

## Task Lifecycle
`queued` ➔ `claimed` ➔ `in_progress` ➔ [`blocked`] ➔ `done` | `failed` | `canceled`

## Task Object (Read)
- `task_id`: (string) Stable unique identifier.
- `project`: "AAS" | "Maelstrom" | "Research".
- `title`: (string) Short summary.
- `description`: (string) Detailed instructions + Acceptance Criteria.
- `task_type`: "feature" | "bug" | "research" | "ui".
- `priority`: "low" | "medium" | "high" | "urgent".
- `status`: Current lifecycle state.
- `inputs`: Array of Artifact objects (context files, snapshots).
- `expected_outputs`: Array of Artifact objects (expected files, reports).

## Event Object (Write)
- `event_id`: (string) Globally unique UUID.
- `task_id`: Reference to parent task.
- `actor`: "Sixth" | "ChatGPT-5.2" | "CodeGPT" | "Linear".
- `event_type`: "claimed" | "progress" | "blocked" | "completed" | "failed".
- `message`: (string) Human/AI readable update.
- `artifacts`: Array of produced Artifact objects.
- `task_version`: (integer) Optimistic concurrency counter.

## Safety & Redaction
- **No Secrets:** Redact `ghp_`, `AIza`, and private keys.
- **Redaction Pattern:** Use `[REDACTED_KEY_TYPE]` for sensitive data.
- **Endpoint:** `NEEDS_INPUT: HANDOFF_BASE_URL`

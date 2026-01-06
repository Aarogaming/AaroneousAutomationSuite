# AgentHandoffProtocol

Implementation of the Agent Handoff Protocol (AAS-212).

## Methods

### `get_handoff_context(self, task_id: str) -> Optional[core.protocol_manager.HandoffObject]`

Retrieve the latest handoff context for a task.

### `relay_handoff(self, handoff: core.protocol_manager.HandoffObject)`

Relay handoff context to the target agent or store it for the next claimant.

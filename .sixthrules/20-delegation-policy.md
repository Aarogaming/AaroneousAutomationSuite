# Delegation & Governance Policy v1.0

## Overview
This policy defines how tasks are delegated between different AI actors and human operators within the AAS ecosystem.

## AI Actors & "I-Called-It" Rule
- **Sixth:** Primary architect and system engineer.
- **ChatGPT-5.2:** Strategic planning and research.
- **CodeGPT:** Targeted code generation and refactoring.

**The First-Come-First-Serve (FCFS) Rule:**
Any AI actor can claim any task from the shared queue. There are no rigid role-based restrictions. The first actor to "call it" by claiming the task in the local registry wins the assignment.

## Delegation & Claiming Process
1. **Check the Board:** Actors must check `handoff/ACTIVE_TASKS.md` for `queued` tasks.
2. **Call It:** The first actor to find a task they are capable of performing must immediately update the task status to `In Progress` and set themselves as the `Assignee`.
3. **Atomic Claiming:** When using the `HandoffManager`, the "Claim-on-Read" pattern ensures that requesting a task automatically assigns it to the requester to prevent race conditions.
4. **Execution:** Once claimed, the actor owns the task until completion, blockage, or failure.

## Handoff Protocol
All delegations must follow the [Handoff Service Contract](./10-handoff-contract.md).
1. Task is queued in `handoff/ACTIVE_TASKS.md` (and optionally synced to Linear).
2. Actor claims the task locally.
3. Actor provides periodic progress events via the `HandoffManager`.
4. Actor submits artifacts to `artifacts/handoff/` and marks task as done.

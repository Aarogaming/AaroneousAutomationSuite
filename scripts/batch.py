"""
Unified batch operations CLI.

Replaces scattered batch helper scripts with a single interface.
"""

from __future__ import annotations

import asyncio
import os
import sys
from pathlib import Path
import click

sys.path.insert(0, str(Path(__file__).parent.parent))

from core.managers import ManagerHub  # noqa: E402


def get_hub() -> ManagerHub:
    return ManagerHub.create()


@click.group()
def cli():
    """Batch operations (submit, status, task)."""
    os.environ.setdefault("PYTHONIOENCODING", "utf-8")


@cli.command()
@click.option("--max", "max_tasks", default=50, show_default=True, help="Maximum tasks to batch")
def submit(max_tasks: int):
    """Submit eligible tasks to batch (aggressive by default)."""
    hub = get_hub()
    if not hub.batch_manager:
        click.echo("Batch API not configured; set OPENAI_API_KEY and retry.")
        raise SystemExit(1)
    batch_id = asyncio.run(hub.tasks.batch_multiple_tasks(max_tasks=max_tasks))
    if batch_id:
        click.echo(f"✓ Batch submitted: {batch_id}")
    else:
        click.echo("No eligible tasks to batch.")


@cli.command()
def status():
    """List active batches."""
    hub = get_hub()
    if not hub.batch_manager:
        click.echo("Batch API not configured; set OPENAI_API_KEY and retry.")
        raise SystemExit(1)
    active = hub.batch_manager.list_active_batches()
    if not active:
        click.echo("No active batches.")
        return
    for batch in active:
        click.echo(f"{batch['id']} | {batch['status']} | meta={batch.get('metadata')}")


@cli.command()
@click.argument("batch_id")
def check(batch_id: str):
    """Check a specific batch."""
    hub = get_hub()
    if not hub.batch_manager:
        click.echo("Batch API not configured; set OPENAI_API_KEY and retry.")
        raise SystemExit(1)
    try:
        status = hub.batch_manager.get_batch_status(batch_id)
        click.echo(f"{batch_id}: {status}")
    except Exception as e:
        click.echo(f"Error: {e}")
        raise SystemExit(1)


@cli.command()
@click.argument("task_id")
def task(task_id: str):
    """Batch a single task."""
    hub = get_hub()
    if not hub.batch_manager:
        click.echo("Batch API not configured; set OPENAI_API_KEY and retry.")
        raise SystemExit(1)
    batch_id = asyncio.run(hub.tasks.batch_task(task_id))
    if batch_id:
        click.echo(f"✓ Task {task_id} batched ({batch_id})")
    else:
        click.echo(f"Failed to batch task {task_id}")


if __name__ == "__main__":
    cli()

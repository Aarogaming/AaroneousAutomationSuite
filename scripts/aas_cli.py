"""
AAS Unified CLI - Modern command-line interface with grouped commands

This is a prototype for the improved CLI structure using Click.
Gradually migrates functionality from task_manager_cli.py with better UX.

Usage:
    python scripts/aas_cli.py task list --status=queued
    python scripts/aas_cli.py task claim AAS-123
    python scripts/aas_cli.py batch status <batch_id>
    python scripts/aas_cli.py workspace scan
    python scripts/aas_cli.py agent roster
    python scripts/aas_cli.py agent help-request AAS-123 <session-id>
"""

import os
import sys
from pathlib import Path
import signal
import socket
import subprocess
import platform
from dotenv import load_dotenv

# Ensure UTF-8 output to avoid Windows charmap errors.
os.environ.setdefault("PYTHONIOENCODING", "utf-8")
try:
    sys.stdout.reconfigure(encoding="utf-8")
    sys.stderr.reconfigure(encoding="utf-8")
except (AttributeError, OSError):
    pass

sys.path.insert(0, str(Path(__file__).parent.parent))

import click
from loguru import logger
from datetime import datetime
from typing import Optional

# Import after path setup
from core.config import find_workspace_env
from core.managers import ManagerHub

PROJECT_ROOT = Path(__file__).parent.parent
PID_FILE = PROJECT_ROOT / "artifacts" / "hub.pid"


def _read_pid() -> Optional[int]:
    try:
        if PID_FILE.exists():
            return int(PID_FILE.read_text(encoding="utf-8").strip())
    except Exception:
        return None
    return None


def _is_running(pid: int) -> bool:
    try:
        os.kill(pid, 0)
        return True
    except Exception:
        return False


@click.group()
@click.option("--debug", is_flag=True, help="Enable debug logging")
@click.option(
    "--config-file", type=click.Path(exists=True), help="Custom config file path"
)
@click.pass_context
def cli(ctx, debug, config_file):
    """
    🚀 AAS Unified CLI - Manage tasks, batches, and workspace health

    Examples:
        aas task list                    # List all tasks
        aas task claim                   # Auto-claim next task
        aas batch submit AAS-123         # Submit task to batch
        aas workspace scan               # Scan workspace health
        aas health                       # Overall system health
    """
    ctx.ensure_object(dict)
    ctx.obj["DEBUG"] = debug
    ctx.obj["hub"] = None

    # Skip heavy init for lightweight commands
    lazy_commands = {"start", "stop", "status", "doctor", "launch"}
    if ctx.invoked_subcommand in lazy_commands:
        return

    # Configure logging
    if debug:
        logger.remove()
        logger.add(sys.stderr, level="DEBUG")

    # Initialize hub
    try:
        ctx.obj["hub"] = ManagerHub.create()
        if debug:
            logger.debug("ManagerHub initialized successfully")
    except Exception as e:
        click.echo(f"❌ Failed to initialize ManagerHub: {e}", err=True)
        if debug:
            raise
        sys.exit(1)


# ============================================================================
# Hub lifecycle (start/stop/status) + doctor
# ============================================================================


@cli.command()
@click.option("--inline-tray", is_flag=True, help="Run Hub and tray in one process")
def start(inline_tray):
    """Start the Hub (detached)."""
    existing = _read_pid()
    if existing and _is_running(existing):
        click.echo(f"Hub already running (pid {existing}).")
        return
    env = os.environ.copy()
    env.setdefault("AAS_LAUNCHED_VIA_TRAY", "1")
    if inline_tray:
        env["AAS_INLINE_TRAY"] = "1"
    try:
        proc = subprocess.Popen(
            [sys.executable, "hub.py"],
            cwd=str(PROJECT_ROOT),
            env=env,
            stdout=subprocess.DEVNULL,
            stderr=subprocess.DEVNULL,
            start_new_session=True,  # avoid tying to terminal session
        )
        click.echo(f"Hub starting (pid {proc.pid}).")
    except Exception as e:
        click.echo(f"Failed to start Hub: {e}", err=True)
        raise SystemExit(1)


@cli.command()
@click.option(
    "--no-clean-temp", is_flag=True, help="Skip temp file cleanup during prep"
)
@click.option(
    "--no-kill-zombies", is_flag=True, help="Skip killing listeners on 50051/8000"
)
@click.option("--wait", is_flag=True, help="Wait for web server readiness after launch")
@click.option(
    "--wait-timeout",
    default=15.0,
    show_default=True,
    help="Seconds to wait when --wait is set",
)
@click.option(
    "--log-max-mb",
    default=100,
    show_default=True,
    help="Rotate hub.log above this size",
)
@click.option("--inline-tray", is_flag=True, help="Start tray inline if available")
def launch(no_clean_temp, no_kill_zombies, wait, wait_timeout, log_max_mb, inline_tray):
    """Prep workspace, run preflight, and start the Hub (launcher)."""
    args = ["launch"]
    if no_clean_temp:
        args.append("--no-clean-temp")
    if no_kill_zombies:
        args.append("--no-kill-zombies")
    if wait:
        args.append("--wait")
        args.extend(["--wait-timeout", str(wait_timeout)])
    if log_max_mb is not None:
        args.extend(["--log-max-mb", str(log_max_mb)])
    if inline_tray:
        args.append("--inline-tray")

    try:
        subprocess.check_call([sys.executable, "scripts/aas_launcher.py", *args])
    except subprocess.CalledProcessError as e:
        click.echo(f"❌ Launcher failed: {e}", err=True)
        raise SystemExit(1)


@cli.command()
def stop():
    """Stop the Hub using the recorded PID."""
    pid = _read_pid()
    if not pid:
        click.echo("No PID file found (Hub may not be running).")
        return
    if not _is_running(pid):
        click.echo("PID file found but process is not running; cleaning up PID file.")
        PID_FILE.unlink(missing_ok=True)
        return
    try:
        os.kill(pid, signal.SIGTERM)
        click.echo(f"Sent SIGTERM to Hub (pid {pid}).")
    except Exception as e:
        click.echo(f"Failed to stop Hub: {e}", err=True)
        raise SystemExit(1)


@cli.command()
def status():
    """Show Hub running status."""
    pid = _read_pid()
    if pid and _is_running(pid):
        click.echo(f"Hub running (pid {pid}).")
    else:
        click.echo("Hub not running.")


@cli.command()
def doctor():
    """Quick environment and dependency check."""
    env_path = find_workspace_env(PROJECT_ROOT)
    if env_path:
        load_dotenv(dotenv_path=env_path, override=False)
    else:
        load_dotenv(dotenv_path=PROJECT_ROOT / ".env", override=False)
    checks = []

    def add(label: str, ok: bool, detail: str = ""):
        checks.append((label, ok, detail))

    add("Python >=3.12", sys.version_info >= (3, 12), platform.python_version())
    add(
        ".env present",
        env_path is not None and env_path.exists(),
        str(env_path) if env_path else "not found",
    )
    add(
        "OPENAI_API_KEY set",
        bool(os.getenv("OPENAI_API_KEY")),
        "missing" if not os.getenv("OPENAI_API_KEY") else "set",
    )

    try:
        import importlib

        importlib.import_module("sqlite_vec")
        add("sqlite-vec", True, "installed")
    except Exception as e:
        add("sqlite-vec", False, str(e))

    for port in (50051, 8000):
        with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as sock:
            sock.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
            try:
                sock.bind(("127.0.0.1", port))
                add(f"Port {port}", True, "available")
            except OSError as e:
                add(f"Port {port}", False, f"in use ({e})")

    click.echo("AAS Doctor:")
    for label, ok, detail in checks:
        status_icon = "✓" if ok else "✖"
        click.echo(f"  {status_icon} {label} ({detail})")

    failures = [c for c in checks if not c[1]]
    if failures:
        raise SystemExit(1)


# ============================================================================
# Task Management Commands
# ============================================================================


@cli.group()
def task():
    """Task management operations (claim, list, status, complete)"""
    pass


@task.command("list")
@click.option(
    "--status",
    type=click.Choice(["queued", "in-progress", "done", "blocked"]),
    help="Filter by task status",
)
@click.option(
    "--priority",
    type=click.Choice(["urgent", "high", "medium", "low"]),
    help="Filter by priority",
)
@click.option("--limit", type=int, default=20, help="Maximum tasks to display")
@click.pass_context
def task_list(ctx, status, priority, limit):
    """List tasks with optional filters"""
    hub = ctx.obj["hub"]

    try:
        _, tasks, _ = hub.guild.parse_board()

        # Apply filters
        if status:
            tasks = [t for t in tasks if t["status"].lower() == status]
        if priority:
            tasks = [t for t in tasks if t["priority"].lower() == priority]

        tasks = tasks[:limit]

        if not tasks:
            click.echo("📋 No tasks found matching criteria")
            return

        click.echo(f"\n📋 Found {len(tasks)} task(s):\n")
        click.echo(f"{'ID':<12} {'Priority':<10} {'Status':<15} {'Title':<40}")
        click.echo("=" * 80)

        for t in tasks:
            # Color-code by priority
            priority_color = {
                "urgent": "red",
                "high": "yellow",
                "medium": "white",
                "low": "cyan",
            }.get(t["priority"].lower(), "white")

            status_icon = {
                "queued": "⏳",
                "in progress": "🔄",
                "done": "✅",
                "blocked": "🚫",
            }.get(t["status"].lower(), "•")

            priority_styled = click.style(t["priority"].upper(), fg=priority_color)
            click.echo(
                f"{t['id']:<12} "
                f"{priority_styled:<10} "
                f"{status_icon} {t['status']:<13} "
                f"{t['title'][:38]}"
            )

        click.echo("")

    except Exception as e:
        click.echo(f"❌ Error listing tasks: {e}", err=True)
        if ctx.obj["DEBUG"]:
            raise
        sys.exit(1)


@task.command("claim")
@click.argument("task_id", required=False)
@click.option("--actor", default="GitHub Copilot", help="Actor claiming the task")
@click.pass_context
def task_claim(ctx, task_id, actor):
    """
    Claim a task (auto-selects next available if no ID provided)

    Examples:
        aas task claim              # Auto-claim next task
        aas task claim AAS-123      # Claim specific task
    """
    hub = ctx.obj["hub"]

    try:
        if task_id:
            result = hub.tasks.claim_task(task_id=task_id, actor_name=actor)
        else:
            result = hub.tasks.claim_task(actor_name=actor)

        if result:
            click.echo("\n✅ Successfully claimed task:")
            click.echo(f"   ID: {result['id']}")
            click.echo(f"   Title: {result['title']}")
            click.echo(f"   Actor: {actor}")
            click.echo(
                f"   Timestamp: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}\n"
            )
        else:
            click.echo("❌ Failed to claim task (may not exist or already claimed)")
            sys.exit(1)

    except Exception as e:
        click.echo(f"❌ Error claiming task: {e}", err=True)
        if ctx.obj["DEBUG"]:
            raise
        sys.exit(1)


@task.command("status")
@click.argument("task_id")
@click.pass_context
def task_status(ctx, task_id):
    """Get detailed status for a specific task"""
    hub = ctx.obj["hub"]

    try:
        status = hub.tasks.get_task_status(task_id)

        if not status:
            click.echo(f"❌ Task {task_id} not found")
            sys.exit(1)

        click.echo(f"\n📊 Task Status: {task_id}\n")
        click.echo(f"{'='*60}")
        click.echo(f"Title:        {status['title']}")
        click.echo(f"Priority:     {status['priority']}")
        click.echo(f"Status:       {status['status']}")
        click.echo(f"Assignee:     {status['assignee']}")
        click.echo(f"Dependencies: {status['depends_on']}")
        click.echo(f"Created:      {status['created']}")
        click.echo(f"Updated:      {status['updated']}")
        click.echo(f"{'='*60}\n")

    except Exception as e:
        click.echo(f"❌ Error getting task status: {e}", err=True)
        if ctx.obj["DEBUG"]:
            raise
        sys.exit(1)


@task.command("complete")
@click.argument("task_id")
@click.pass_context
def task_complete(ctx, task_id):
    """Mark a task as completed"""
    hub = ctx.obj["hub"]

    try:
        success = hub.tasks.complete_task(task_id)

        if success:
            click.echo(f"✅ Task {task_id} marked as complete")
        else:
            click.echo(f"❌ Failed to complete task {task_id}")
            sys.exit(1)

    except Exception as e:
        click.echo(f"❌ Error completing task: {e}", err=True)
        if ctx.obj["DEBUG"]:
            raise
        sys.exit(1)


# ============================================================================
# Batch Processing Commands
# ============================================================================


@cli.group()
def batch():
    """Batch processing operations (submit, status, results)"""
    pass


@batch.command("submit")
@click.argument("task_ids", nargs=-1, required=True)
@click.option("--description", help="Batch description")
@click.pass_context
def batch_submit(ctx, task_ids, description):
    """
    Submit tasks to OpenAI Batch API

    Example:
        aas batch submit AAS-123 AAS-124 AAS-125
    """
    hub = ctx.obj["hub"]

    try:
        click.echo(f"🚀 Submitting {len(task_ids)} task(s) to batch processing...")

        # Use asyncio to run async batch operation
        import asyncio

        async def submit_all():
            results = []
            for task_id in task_ids:
                batch_id = await hub.tasks.batch_task(task_id)
                results.append((task_id, batch_id))
            return results

        results = asyncio.run(submit_all())

        click.echo("\n✅ Batch submission complete:\n")
        for task_id, batch_id in results:
            click.echo(f"   {task_id} → {batch_id}")
        click.echo("")

    except Exception as e:
        click.echo(f"❌ Error submitting batch: {e}", err=True)
        if ctx.obj["DEBUG"]:
            raise
        sys.exit(1)


@batch.command("status")
@click.argument("batch_id")
@click.pass_context
def batch_status(ctx, batch_id):
    """Get status of a batch job"""
    hub = ctx.obj["hub"]

    try:
        status = hub.batch.get_status(batch_id)

        click.echo(f"\n📊 Batch Status: {batch_id}\n")
        click.echo(f"{'='*60}")
        click.echo(f"Status:         {status['status']}")
        click.echo(f"Total Requests: {status['request_counts']['total']}")
        click.echo(f"Completed:      {status['request_counts']['completed']}")
        click.echo(f"Failed:         {status['request_counts']['failed']}")
        click.echo(f"Created:        {status['created_at']}")
        if status["completed_at"]:
            click.echo(f"Completed:      {status['completed_at']}")
        click.echo(f"{'='*60}\n")

    except Exception as e:
        click.echo(f"❌ Error getting batch status: {e}", err=True)
        if ctx.obj["DEBUG"]:
            raise
        sys.exit(1)


# ============================================================================
# Workspace Management Commands
# ============================================================================


@cli.group()
def workspace():
    """Workspace health and cleanup operations"""
    pass


@workspace.command("scan")
@click.pass_context
def workspace_scan(ctx):
    """Scan workspace for health issues"""
    hub = ctx.obj["hub"]

    try:
        click.echo("🔍 Scanning workspace...\n")

        # Scan for duplicates
        duplicates = hub.workspace.find_duplicates()
        if duplicates:
            click.echo(f"⚠️  Found {len(duplicates)} sets of duplicate files")

        # Scan for large files
        large_files = hub.workspace.find_large_files(min_size_mb=10)
        if large_files:
            click.echo(f"📦 Found {len(large_files)} large files (>10MB)")

        # Overall health
        health = hub.get_health_summary()
        status_icon = {"healthy": "✅", "degraded": "⚠️", "error": "❌"}.get(
            health["overall_status"], "•"
        )

        click.echo(f"\n{status_icon} Overall Status: {health['overall_status']}\n")

    except Exception as e:
        click.echo(f"❌ Error scanning workspace: {e}", err=True)
        if ctx.obj["DEBUG"]:
            raise
        sys.exit(1)


@workspace.command("defrag")
@click.option("--dry-run", is_flag=True, help="Show what would be moved")
@click.pass_context
def workspace_defrag(ctx, dry_run):
    """Consolidate workspace structure (builds, audits, docs)"""
    hub = ctx.obj["hub"]

    try:
        action = "DRY RUN: Would defrag" if dry_run else "Defragmenting"
        click.echo(f"🏗️  {action} workspace...")

        results = hub.workspace.defrag_workspace(dry_run=dry_run)

        if not results:
            click.echo("✅ Workspace already optimized.")
            return

        for res in results:
            click.echo(f"  • {res}")

    except Exception as e:
        click.echo(f"❌ Error defragmenting workspace: {e}", err=True)
        if ctx.obj["DEBUG"]:
            raise
        sys.exit(1)


@workspace.command("cleanup")
@click.option("--dry-run", is_flag=True, help="Show what would be deleted")
@click.pass_context
def workspace_cleanup(ctx, dry_run):
    """Remove duplicate and temporary files"""
    hub = ctx.obj["hub"]

    try:
        click.echo(f"🧹 Cleaning up workspace {'(DRY RUN)' if dry_run else ''}...")

        deleted_dupes = hub.workspace.cleanup_duplicates(dry_run=dry_run)
        deleted_temp = hub.workspace.cleanup_temp_files(dry_run=dry_run)

        click.echo("\n✅ Cleanup complete:")
        click.echo(f"   - Removed {len(deleted_dupes)} duplicate files")
        click.echo(f"   - Removed {len(deleted_temp)} temporary files\n")

    except Exception as e:
        click.echo(f"❌ Error cleaning workspace: {e}", err=True)
        if ctx.obj["DEBUG"]:
            raise
        sys.exit(1)


@workspace.command("audit")
@click.pass_context
def workspace_audit(ctx):
    """Run AI-readiness audit (type hints, docstrings)"""
    hub = ctx.obj["hub"]

    try:
        click.echo("\n🔍 Running AI-Readiness Audit...")
        from core.batch_gen import TaskGenerator

        # Mocking dependencies for audit
        tg = TaskGenerator(None, None, hub.config)

        import asyncio

        async def run_audit():
            return await tg.suggest_improvements()

        suggestions = asyncio.run(run_audit())
        ai_tasks = [s for s in suggestions if s.get("type") == "ai_readiness"]

        if ai_tasks:
            click.echo(f"Found {len(ai_tasks)} AI-readiness gaps:")
            for task in ai_tasks:
                click.echo(f"  - {task['title']}")
                click.echo(f"    {task['description']}")
        else:
            click.echo("✅ No AI-readiness gaps found!")
        click.echo("")

    except Exception as e:
        click.echo(f"❌ Error auditing workspace: {e}", err=True)
        if ctx.obj["DEBUG"]:
            raise
        sys.exit(1)


# ============================================================================
# Multi-Client Commands
# ============================================================================


@cli.group()
def client():
    """Multi-client operations (register, heartbeat)"""
    pass


@client.command("heartbeat")
@click.option("--client-id", help="Custom client ID")
@click.pass_context
def client_heartbeat(ctx, client_id):
    """Start client heartbeat loop"""
    hub = ctx.obj["hub"]

    import socket
    import platform
    import asyncio

    if not client_id:
        client_id = f"client-{socket.gethostname()}-{platform.system().lower()}"

    hostname = socket.gethostname()
    click.echo(f"\n💓 Starting heartbeat for {client_id}...")

    hub.tasks.register_client(client_id, hostname)

    try:
        import psutil
    except ImportError:
        psutil = None
        click.echo("⚠️  psutil not found, metrics will be limited.")

    async def run_loop():
        while True:
            cpu = int(psutil.cpu_percent()) if psutil else 0
            mem = int(psutil.virtual_memory().percent) if psutil else 0

            hub.tasks.update_heartbeat(client_id, cpu, mem)
            hub.tasks.check_client_timeouts()

            click.echo(
                f"  [Heartbeat] {datetime.now().strftime('%H:%M:%S')} - CPU: {cpu}% MEM: {mem}%",
                nl=False,
            )
            click.echo("\r", nl=False)
            await asyncio.sleep(30)

    try:
        asyncio.run(run_loop())
    except KeyboardInterrupt:
        click.echo("\n🛑 Heartbeat stopped by user")


# ============================================================================
# Agent Collaboration Commands
# ============================================================================


@cli.group()
def agent():
    """Agent collaboration operations (check-in, help requests, roster)"""
    pass


@agent.command("checkin")
@click.argument("agent_name")
@click.option("--version", help="Agent version")
@click.pass_context
def agent_checkin(ctx, agent_name, version):
    """Check in as an active agent"""
    hub = ctx.obj["hub"]

    try:
        session_id = hub.collaboration.check_in(agent_name, agent_version=version)
        click.echo(f"✅ Checked in as {agent_name}")
        click.echo(f"   Session ID: {session_id}")
        click.echo(f"\n💡 Remember to run 'aas agent checkout {session_id}' when done")
    except Exception as e:
        click.echo(f"❌ Check-in failed: {e}", err=True)
        if ctx.obj["DEBUG"]:
            raise
        sys.exit(1)


@agent.command("checkout")
@click.argument("session_id")
@click.pass_context
def agent_checkout(ctx, session_id):
    """Check out from active session"""
    hub = ctx.obj["hub"]

    try:
        hub.collaboration.check_out(session_id)
        click.echo(f"👋 Checked out from session {session_id}")
    except Exception as e:
        click.echo(f"❌ Check-out failed: {e}", err=True)
        if ctx.obj["DEBUG"]:
            raise
        sys.exit(1)


@agent.command("roster")
@click.pass_context
def agent_roster(ctx):
    """Show active agent roster with capabilities"""
    hub = ctx.obj["hub"]

    try:
        agents = hub.collaboration.get_active_agents()

        if not agents:
            click.echo("📋 No active agents")
            return

        click.echo(f"\n🤝 Active Agent Roster ({len(agents)} agent(s)):\n")

        for agent in agents:
            caps = agent["capabilities"]
            strengths = ", ".join(caps.get("strengths", [])[:3])
            context_size = caps.get("context_window", "medium")

            click.echo(f"  {agent['agent_name']}")
            click.echo(f"    Session: {agent['session_id']}")
            click.echo(f"    Strengths: {strengths}")
            click.echo(f"    Context: {context_size}")
            click.echo(f"    Workload: {agent['active_tasks']} active task(s)")
            if agent["current_task"]:
                click.echo(f"    Current: {agent['current_task']}")
            click.echo()

    except Exception as e:
        click.echo(f"❌ Error fetching roster: {e}", err=True)
        if ctx.obj["DEBUG"]:
            raise
        sys.exit(1)


@agent.command("help-request")
@click.argument("task_id")
@click.argument("session_id")
@click.option(
    "--type",
    "help_type",
    required=True,
    type=click.Choice(
        ["code_review", "debugging", "architecture", "testing", "refactoring"]
    ),
    help="Type of help needed",
)
@click.option(
    "--urgency",
    default="medium",
    type=click.Choice(["low", "medium", "high", "critical"]),
    help="Request urgency",
)
@click.option("--context", prompt=True, help="Describe what help is needed")
@click.option("--estimated-time", type=int, help="Estimated minutes needed")
@click.pass_context
def help_request(ctx, task_id, session_id, help_type, urgency, context, estimated_time):
    """Request help from other agents on a task"""
    hub = ctx.obj["hub"]

    try:
        request_id = hub.collaboration.request_help(
            task_id=task_id,
            requester_session_id=session_id,
            help_type=help_type,
            context=context,
            urgency=urgency,
            estimated_time=estimated_time,
        )
        click.echo(f"🆘 Help request created: {request_id}")
        click.echo(f"   Type: {help_type}")
        click.echo(f"   Urgency: {urgency}")
        if estimated_time:
            click.echo(f"   Estimated: {estimated_time} minutes")
    except Exception as e:
        click.echo(f"❌ Help request failed: {e}", err=True)
        if ctx.obj["DEBUG"]:
            raise
        sys.exit(1)


@agent.command("help-list")
@click.pass_context
def help_list(ctx):
    """List open help requests"""
    hub = ctx.obj["hub"]

    try:
        requests = hub.collaboration.get_open_help_requests()

        if not requests:
            click.echo("📋 No open help requests")
            return

        click.echo(f"\n🆘 Open Help Requests ({len(requests)}):\n")

        for req in requests:
            urgency_color = {
                "low": "green",
                "medium": "yellow",
                "high": "red",
                "critical": "bright_red",
            }.get(req["urgency"], "white")

            urgency_display = click.style(req["urgency"].upper(), fg=urgency_color)

            click.echo(f"  [{req['id']}]")
            click.echo(f"    Task: {req['task_id']}")
            click.echo(f"    From: {req['requester']}")
            click.echo(f"    Type: {req['help_type']}")
            click.echo(f"    Urgency: {urgency_display}")
            click.echo(f"    Context: {req['context'][:80]}...")
            if req["estimated_time"]:
                click.echo(f"    Estimated: {req['estimated_time']} min")
            click.echo()

    except Exception as e:
        click.echo(f"❌ Error fetching help requests: {e}", err=True)
        if ctx.obj["DEBUG"]:
            raise
        sys.exit(1)


@agent.command("help-accept")
@click.argument("request_id")
@click.argument("session_id")
@click.option("--message", help="Optional response message")
@click.pass_context
def help_accept(ctx, request_id, session_id, message):
    """Accept a help request"""
    hub = ctx.obj["hub"]

    try:
        success = hub.collaboration.accept_help_request(
            request_id=request_id,
            helper_session_id=session_id,
            response_message=message,
        )

        if success:
            click.echo(f"🤝 Help request accepted: {request_id}")
            if message:
                click.echo(f"   Message: {message}")
        else:
            click.echo("❌ Could not accept help request (already taken or invalid)")
            sys.exit(1)
    except Exception as e:
        click.echo(f"❌ Error accepting help request: {e}", err=True)
        if ctx.obj["DEBUG"]:
            raise
        sys.exit(1)


@agent.command("help-complete")
@click.argument("request_id")
@click.option("--outcome", prompt=True, help="Summary of outcome")
@click.pass_context
def help_complete(ctx, request_id, outcome):
    """Mark help request as completed"""
    hub = ctx.obj["hub"]

    try:
        hub.collaboration.complete_help_request(request_id, outcome)
        click.echo(f"✅ Help request completed: {request_id}")
        click.echo(f"   Outcome: {outcome}")
    except Exception as e:
        click.echo(f"❌ Error completing help request: {e}", err=True)
        if ctx.obj["DEBUG"]:
            raise
        sys.exit(1)


@agent.command("find-agent")
@click.option("--task-desc", prompt=True, help="Task description")
@click.option("--tags", help="Comma-separated task tags")
@click.pass_context
def find_agent(ctx, task_desc, tags):
    """Find best available agent for a task"""
    hub = ctx.obj["hub"]

    try:
        task_tags = tags.split(",") if tags else []
        best_agent = hub.collaboration.find_best_agent_for_task(task_desc, task_tags)

        if not best_agent:
            click.echo("❌ No suitable agents available")
            return

        click.echo("\n✅ Best Match Found:")
        click.echo(f"  Agent: {best_agent['agent_name']}")
        click.echo(f"  Session: {best_agent['session_id']}")
        click.echo(f"  Match Score: {int(best_agent['match_score']*100)}%")
        click.echo(f"  Current Workload: {best_agent['active_tasks']} task(s)")

        caps = best_agent["capabilities"]
        click.echo(f"  Strengths: {', '.join(caps.get('strengths', []))}")
        click.echo(f"  Best For: {', '.join(caps.get('best_for', []))}")

    except Exception as e:
        click.echo(f"❌ Error finding agent: {e}", err=True)
        if ctx.obj["DEBUG"]:
            raise
        sys.exit(1)


# ============================================================================
# System Health Command
# ============================================================================


@cli.command("health")
@click.option("--json", "output_json", is_flag=True, help="Output as JSON")
@click.pass_context
def system_health(ctx, output_json):
    """Get overall system health status"""
    hub = ctx.obj["hub"]

    try:
        health = hub.get_health_summary()
        validation = hub.validate_all()

        if output_json:
            import json

            click.echo(json.dumps({**health, "validation": validation}, indent=2))
        else:
            click.echo("\n🏥 AAS System Health Report\n")
            click.echo(f"{'='*60}")
            click.echo(f"Timestamp: {health['timestamp']}")
            click.echo(f"Overall:   {health['overall_status'].upper()}")
            click.echo("\nManager Status:")

            for name, status in validation.items():
                icon = "✅" if status else "❌"
                click.echo(
                    f"  {icon} {name.capitalize():<15} {'OK' if status else 'FAILED'}"
                )

            metrics = health.get("metrics", {})
            components = health.get("components", {})

            click.echo("\nServices:")
            click.echo(
                f"  Web: {components.get('web', 'unknown')} | IPC: {components.get('ipc', 'unknown')} | DB: {components.get('database', 'unknown')}"
            )
            click.echo(
                f"  Artifacts writable: {metrics.get('artifacts_writable', True)} | Disk free: {metrics.get('disk_free_gb')} GB ({metrics.get('disk_free_pct')}%)"
            )

            tasks = metrics.get("tasks", {})
            if tasks:
                click.echo(
                    f"\nTasks: queued={tasks.get('queued', 0)} in_progress={tasks.get('in_progress', 0)} done={tasks.get('done', 0)} total={tasks.get('total', 0)}"
                )

            plugins = metrics.get("plugins", {})
            if plugins:
                click.echo(f"Plugins: {plugins.get('count', 0)} enabled")

            batch = metrics.get("batch", {})
            if batch:
                click.echo(
                    f"Batch: {'enabled' if batch.get('enabled') else 'disabled'} | auto-monitor={batch.get('auto_monitor', False)}"
                )

            workspace_extra = metrics.get("workspace_extra", {})
            large_files = workspace_extra.get("large_files") or metrics.get(
                "large_files"
            )
            if large_files:
                click.echo("\nLarge artifacts (>=200MB):")
                for lf in large_files:
                    click.echo(f"  - {lf['path']} ({lf['size_mb']} MB)")

            click.echo(f"{'='*60}\n")

    except Exception as e:
        click.echo(f"❌ Error getting health status: {e}", err=True)
        if ctx.obj["DEBUG"]:
            raise
        sys.exit(1)


# ============================================================================
# Migration Helper
# ============================================================================


@cli.command("migrate-from-old-cli", hidden=True)
@click.pass_context
def migrate_from_old(ctx):
    """Helper command showing migration from old CLI"""
    click.echo("\n📚 CLI Migration Guide\n")
    click.echo("Old Command → New Command")
    click.echo("=" * 60)
    click.echo("task_manager_cli.py list-unbatched")
    click.echo("  → aas task list --status=queued")
    click.echo("")
    click.echo("task_manager_cli.py claim")
    click.echo("  → aas task claim")
    click.echo("")
    click.echo("task_manager_cli.py batch AAS-123")
    click.echo("  → aas batch submit AAS-123")
    click.echo("")
    click.echo("task_manager_cli.py workspace-scan")
    click.echo("  → aas workspace scan")
    click.echo("")
    click.echo("task_manager_cli.py health")
    click.echo("  → aas health")
    click.echo("=" * 60 + "\n")


if __name__ == "__main__":
    cli(obj={})

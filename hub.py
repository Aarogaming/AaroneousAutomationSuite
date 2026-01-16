import asyncio
import sys
import uvicorn
import os
import threading
import webbrowser
import contextlib
import signal
import atexit
from loguru import logger
from typing import Optional
from pathlib import Path
import hashlib
import json
import time
from core.config import load_config
from core.ipc_server import serve_ipc
from core.web_server import create_app
from core.preflight import run_preflight
from core.grpc_service import serve_grpc

try:
    from PIL import Image, ImageDraw
    import pystray
except Exception:
    Image = None
    ImageDraw = None
    pystray = None


class TaskCLI:
    """CLI interface for task management operations"""

    def __init__(self, task_manager):
        self.task_manager = task_manager

    def create_task(
        self,
        title: str,
        priority: str = "Medium",
        depends: Optional[str] = None,
        description: Optional[str] = None,
    ):
        """Create a new task"""
        new_id = self.task_manager.add_task(
            priority=priority,
            title=title,
            description=description or title,
            depends_on=depends or "-",
        )
        print(f"\n[OK] Created task {new_id}: {title}")
        print(f"     Priority: {priority} | Dependencies: {depends or '-'}\n")
        return new_id

    def start_task(self, task_id: str, actor: str = "Copilot"):
        """Start (claim) a task"""
        task = self.task_manager.claim_task(task_id=task_id, actor_name=actor)
        if not task:
            print(f"\n[ERROR] Task {task_id} not found or cannot be claimed\n")
            return False

        print(f"\n[OK] Task {task_id} claimed by {actor}")
        print(f"     Title: {task['title']}")
        print(f"     Artifacts: artifacts/guild/{task_id}/\n")
        return True

    def complete_task(self, task_id: str):
        """Mark task as complete"""
        return self.task_manager.complete_task(task_id)

    def list_tasks(
        self,
        status: Optional[str] = None,
        priority: Optional[str] = None,
        assignee: Optional[str] = None,
    ):
        """List tasks with optional filters"""
        if not self.task_manager.guild:
            print("\n[ERROR] Guild board not available\n")
            return

        _, tasks, _ = self.task_manager.guild.parse_board()

        # Apply filters
        filtered = tasks
        if status:
            filtered = [t for t in filtered if t["status"].lower() == status.lower()]
        if priority:
            filtered = [
                t for t in filtered if t["priority"].lower() == priority.lower()
            ]
        if assignee:
            filtered = [
                t
                for t in filtered
                if t.get("assignee", "-").lower() == assignee.lower()
            ]

        if not filtered:
            print("\n[!] No tasks match the filters\n")
            return

        print(f"\nTASKS ({len(filtered)} found)")
        print("-" * 100)
        print(
            f"{'ID':<12} | {'Priority':<10} | {'Status':<14} | {'Assignee':<12} | {'Title'}"
        )
        print("-" * 100)

        for t in filtered:
            assignee_display = t.get("assignee", "-")
            print(
                f"{t['id']:<12} | {t['priority']:<10} | {t['status']:<14} | {assignee_display:<12} | {t['title'][:50]}"
            )

        print("-" * 100 + "\n")

    def show_task(self, task_id: str):
        """Show full task details"""
        status = self.task_manager.get_task_status(task_id)
        if "error" in status:
            print(f"\n[ERROR] {status['error']}\n")
            return

        print(f"\nTASK DETAILS: {task_id}")
        print("=" * 80)
        print(f"Title:        {status['title']}")
        print(f"Priority:     {status['priority']}")
        print(f"Status:       {status['status']}")
        print(f"Assignee:     {status.get('assignee', 'Unassigned')}")
        print(f"Dependencies: {status.get('depends_on', 'None')}")
        print(f"Created:      {status.get('created', 'Unknown')}")
        print(f"Updated:      {status.get('updated', 'Unknown')}")
        print("=" * 80 + "\n")

    def available_tasks(self):
        """Show tasks that can be claimed (queued with met dependencies)"""
        task = self.task_manager.find_next_claimable_task()

        if not task:
            print("\n[!] No tasks available to claim right now\n")
            return

        print("\nNEXT AVAILABLE TASK")
        print("-" * 100)
        print(f"ID:       {task['id']}")
        print(f"Priority: {task['priority']}")
        print(f"Title:    {task['title']}")
        print("-" * 100)
        print(f"\nUse: python hub.py task start {task['id']} [actor_name]\n")


async def main():
    # Single-process mode by default; disable with --no-tray
    inline_tray = True
    if "--no-tray" in sys.argv:
        inline_tray = False
        sys.argv = [a for a in sys.argv if a != "--no-tray"]

    def create_inline_tray_icon():
        """Create a lightweight tray icon for inline mode."""
        if Image is None or ImageDraw is None:
            return None
        size = 64
        img = Image.new("RGBA", (size, size), color=(0, 0, 0, 0))
        draw = ImageDraw.Draw(img)
        draw.ellipse([0, 0, size - 1, size - 1], fill=(67, 56, 202))
        margin = int(size * 0.15)
        letter_width = size - (2 * margin)
        letter_height = int(size * 0.7)
        top = int(size * 0.15)
        left = margin
        peak_x = size // 2
        left_bottom = (left, top + letter_height)
        right_bottom = (left + letter_width, top + letter_height)
        draw.polygon([(peak_x, top), left_bottom, right_bottom], fill="white")
        inner_offset = int(size * 0.12)
        draw.polygon(
            [
                (peak_x, top + int(inner_offset * 1.5)),
                (left_bottom[0] + inner_offset, left_bottom[1] - inner_offset),
                (right_bottom[0] - inner_offset, right_bottom[1] - inner_offset),
            ],
            fill=(67, 56, 202),
        )
        bar_y = top + int(letter_height * 0.6)
        bar_thickness = int(size * 0.08)
        bar_left = left + int(letter_width * 0.25)
        bar_right = left + int(letter_width * 0.75)
        draw.rectangle(
            [bar_left, bar_y, bar_right, bar_y + bar_thickness], fill="white"
        )
        return img

    def start_inline_tray(loop: asyncio.AbstractEventLoop):
        """Start tray UI in a background thread within the same process."""
        if pystray is None:
            logger.warning(
                "Tray UI unavailable (missing pystray/Pillow); continuing without tray UI."
            )
            return None
        if os.getenv("WSL_DISTRO_NAME"):
            logger.info(
                "Tray skipped: WSL environment detected (no native system tray)."
            )
            return None
        if os.name != "nt":
            if not os.getenv("DISPLAY"):
                logger.info("Tray skipped: no system tray detected (DISPLAY unset).")
                return None

        icon_img = create_inline_tray_icon()
        if not icon_img:
            logger.warning("Inline tray icon could not be created; skipping tray UI.")
            return None

        def open_dashboard(icon, item):
            try:
                webbrowser.open("http://localhost:8000")
            except Exception as e:
                logger.warning(f"Failed to open dashboard: {e}")

        def quit_hub(icon, item):
            logger.info("Inline tray quit requested; terminating Hub.")
            os._exit(0)

        menu = pystray.Menu(
            pystray.MenuItem("Open Dashboard", open_dashboard),
            pystray.MenuItem("Quit Hub", quit_hub),
        )
        tray_icon = pystray.Icon("AAS Hub", icon_img, "AAS Hub", menu)

        def run_icon():
            try:
                tray_icon.run()
            except Exception as e:
                logger.warning(f"Inline tray terminated: {e}")

        thread = threading.Thread(target=run_icon, daemon=True)
        thread.start()
        logger.info("Inline tray started (single-process mode).")
        return tray_icon

    # Configure logging (console + rotating file)
    log_file = Path("artifacts/hub.log")
    try:
        # If log file is locked, fall back to a unique name
        test_handle = open(log_file, "a", encoding="utf-8")
        test_handle.close()
    except Exception:
        log_file = Path(f"artifacts/hub_{int(time.time())}.log")
    log_file.parent.mkdir(parents=True, exist_ok=True)
    logger.remove()
    log_format = "{time:YYYY-MM-DD HH:mm:ss} | {level:<8} | {message}"
    logger.add(sys.stderr, level="INFO", format=log_format, enqueue=True)
    logger.add(
        log_file,
        rotation="10 MB",
        retention="10 days",
        level="DEBUG",
        format=log_format,
        enqueue=True,
    )

    logger.info("Initializing Aaroneous Automation Suite (AAS) Hub...")

    # 1. Load Resilient Configuration
    try:
        config = load_config()
    except Exception:
        logger.critical("Failed to load configuration. Hub cannot start.")
        return

    # 1a. Preflight checks (ports, dependencies, workspace hygiene)
    web_host = os.getenv("AAS_WEB_HOST", "0.0.0.0")
    try:
        web_port = int(os.getenv("AAS_WEB_PORT", "8000"))
    except ValueError:
        web_port = 8000
    preflight = run_preflight(
        config=config, workspace_root=Path.cwd(), web_host=web_host, web_port=web_port
    )
    preflight.log()
    if os.getenv("AAS_FORCE_PYTHON"):
        preflight.needs_reexec = False

    if (
        preflight.needs_reexec
        and preflight.preferred_python
        and not os.getenv("AAS_PREFLIGHT_REEXEC")
    ):
        try:
            new_env = os.environ.copy()
            new_env["AAS_PREFLIGHT_REEXEC"] = "1"
            python_path = str(preflight.preferred_python)
            logger.info(f"Re-launching Hub with workspace Python at {python_path}")
            os.execve(python_path, [python_path] + sys.argv, new_env)
        except Exception as e:
            logger.warning(
                f"Preflight re-launch with workspace Python failed, continuing: {e}"
            )
    if preflight.issues:
        logger.critical("Startup blocked by preflight issues; resolve above and retry.")
        return
    web_host = preflight.web_host
    web_port = preflight.web_port
    config.ipc_port = preflight.ipc_port
    resolved_ipc_ports = preflight.ipc_ports

    # 1c. Persist runtime metadata for discovery (tray/dashboard/tests)
    try:
        runtime_file = Path("artifacts/runtime.json")
        runtime_file.parent.mkdir(parents=True, exist_ok=True)
        runtime = {
            "web_host": web_host,
            "web_port": web_port,
            "ws_url": f"ws://{web_host}:{web_port}/ws/events",
            "ipc_ports": resolved_ipc_ports,
            "ipc_port": preflight.ipc_port,
            "venv": sys.executable,
            "env": {
                "AAS_WEB_HOST": os.getenv("AAS_WEB_HOST"),
                "AAS_WEB_PORT": os.getenv("AAS_WEB_PORT"),
                "AAS_GRPC_PORT": os.getenv("AAS_GRPC_PORT"),
            },
            "pid_file": str(Path("artifacts/hub.pid").resolve()),
        }
        runtime_file.write_text(json.dumps(runtime, indent=2), encoding="utf-8")
    except Exception as e:
        logger.warning(f"Failed to write runtime metadata: {e}")

    # 1b. Single-instance guard + PID file for unified start/stop tooling
    def _pid_alive(pid: int) -> bool:
        try:
            if os.name == "nt":
                # Windows-specific check
                import ctypes

                PROCESS_QUERY_INFORMATION = 0x0400
                PROCESS_VM_READ = 0x0010
                handle = ctypes.windll.kernel32.OpenProcess(
                    PROCESS_QUERY_INFORMATION | PROCESS_VM_READ, False, pid
                )
                if handle == 0:
                    return False
                ctypes.windll.kernel32.CloseHandle(handle)
                return True
            else:
                os.kill(pid, 0)
                return True
        except Exception:
            return False

    pid_file = Path("artifacts/hub.pid")
    if pid_file.exists():
        try:
            existing = int(pid_file.read_text(encoding="utf-8").strip())
            if existing and existing != os.getpid() and _pid_alive(existing):
                logger.critical(
                    f"Another Hub appears to be running (PID {existing}); aborting startup."
                )
                # Auto-recovery: if it's a stale PID file, we'll overwrite it later
                # but if it's actually alive, we must stop.
                return
        except Exception:
            # Corrupt PID file, safe to ignore and overwrite
            pass

    # Register cleanup handlers for PID file
    def cleanup_pid_file():
        try:
            current_pid = str(os.getpid())
            if (
                pid_file.exists()
                and pid_file.read_text(encoding="utf-8").strip() == current_pid
            ):
                pid_file.unlink()
                logger.debug("Cleaned up PID file")
        except Exception as e:
            logger.warning(f"Failed to clean up PID file: {e}")

    def signal_handler(signum, frame):
        logger.info(f"Received signal {signum}, cleaning up...")
        cleanup_pid_file()
        sys.exit(0)

    # Register cleanup on normal exit and signals
    atexit.register(cleanup_pid_file)
    signal.signal(signal.SIGINT, signal_handler)
    signal.signal(signal.SIGTERM, signal_handler)

    try:
        pid_file.write_text(str(os.getpid()), encoding="utf-8")
        logger.debug(f"Wrote PID file to {pid_file}")
    except Exception as e:
        logger.warning(f"Failed to write PID file: {e}")

    # 2. Initialize Manager Hub (Unified access to all managers)
    from core.managers import ManagerHub

    hub = ManagerHub.create(config=config)
    # Initialize GitHub integration (webhooks/poller/openai reconcile)
    try:
        from core.github_integration import GitHubIntegration

        hub.github = GitHubIntegration(
            db_path="artifacts/github/github_events.db", ws_manager=hub.ws
        )
    except Exception as e:
        hub.github = None
        logger.warning(f"GitHub integration not initialized: {e}")
    # Git sync helper (manual trigger)
    try:
        from core.git_sync import GitSync

        hub.git_sync = GitSync(repo_path=str(Path.cwd()), ws_manager=hub.ws)
    except Exception as e:
        hub.git_sync = None
        logger.warning(f"Git sync not initialized: {e}")
    # Log GitHub App env readiness
    missing_env = []
    for var in [
        "GITHUB_APP_ID",
        "GITHUB_APP_INSTALLATION_ID",
        "GITHUB_APP_PRIVATE_KEY",
    ]:
        if not os.getenv(var):
            missing_env.append(var)
    if missing_env:
        logger.warning(f"GitHub App sync env vars missing: {', '.join(missing_env)}")
    # Initialize GitHub integration (webhooks/poller/openai reconcile)
    try:
        from core.github_integration import GitHubIntegration

        hub.github = GitHubIntegration(
            db_path="artifacts/github/github_events.db", ws_manager=hub.ws
        )
    except Exception as e:
        hub.github = None
        logger.warning(f"GitHub integration not initialized: {e}")

    # 3. Initialize Task CLI
    task_cli = TaskCLI(hub.tasks)

    # 3b. Start inline tray if requested (single-process mode)
    if inline_tray:
        try:
            start_inline_tray(asyncio.get_running_loop())
        except Exception as e:
            logger.warning(f"Inline tray failed to start: {e}")

    # Handle CLI commands
    if len(sys.argv) > 1:
        cmd = sys.argv[1].lower()

        # Task management subcommands
        if cmd == "task":
            if len(sys.argv) < 3:
                print("\nUsage: python hub.py task <command> [args]")
                print("\nCommands:")
                print(
                    "  create <title> [--priority High] [--depends AAS-001,AAS-002] [--description 'text']"
                )
                print("  start <task_id> [actor_name]")
                print("  complete <task_id>")
                print("  list [--status queued] [--priority High] [--assignee Copilot]")
                print("  show <task_id>")
                print("  available")
                print("\n")
                return

            subcmd = sys.argv[2].lower()

            if subcmd == "create":
                if len(sys.argv) < 4:
                    print(
                        "\nUsage: python hub.py task create <title> [--priority High] [--depends AAS-001]\n"
                    )
                    return

                title = sys.argv[3]
                priority = "Medium"
                depends = None
                description = None

                # Parse optional args
                i = 4
                while i < len(sys.argv):
                    if sys.argv[i] == "--priority" and i + 1 < len(sys.argv):
                        priority = sys.argv[i + 1]
                        i += 2
                    elif sys.argv[i] == "--depends" and i + 1 < len(sys.argv):
                        depends = sys.argv[i + 1]
                        i += 2
                    elif sys.argv[i] == "--description" and i + 1 < len(sys.argv):
                        description = sys.argv[i + 1]
                        i += 2
                    else:
                        i += 1

                task_cli.create_task(title, priority, depends, description)

            elif subcmd == "start":
                if len(sys.argv) < 4:
                    print("\nUsage: python hub.py task start <task_id> [actor_name]\n")
                    return
                task_id = sys.argv[3]
                actor = sys.argv[4] if len(sys.argv) > 4 else "Copilot"
                task_cli.start_task(task_id, actor)

            elif subcmd == "complete":
                if len(sys.argv) < 4:
                    print("\nUsage: python hub.py task complete <task_id>\n")
                    return
                task_id = sys.argv[3]
                if task_cli.complete_task(task_id):
                    print(f"\n[OK] Task {task_id} marked as Done\n")
                else:
                    print(f"\n[ERROR] Task {task_id} not found or already completed\n")

            elif subcmd == "list":
                status = None
                priority = None
                assignee = None

                i = 3
                while i < len(sys.argv):
                    if sys.argv[i] == "--status" and i + 1 < len(sys.argv):
                        status = sys.argv[i + 1]
                        i += 2
                    elif sys.argv[i] == "--priority" and i + 1 < len(sys.argv):
                        priority = sys.argv[i + 1]
                        i += 2
                    elif sys.argv[i] == "--assignee" and i + 1 < len(sys.argv):
                        assignee = sys.argv[i + 1]
                        i += 2
                    else:
                        i += 1

                task_cli.list_tasks(status, priority, assignee)

            elif subcmd == "show":
                if len(sys.argv) < 4:
                    print("\nUsage: python hub.py task show <task_id>\n")
                    return
                task_id = sys.argv[3]
                task_cli.show_task(task_id)

            elif subcmd == "available":
                task_cli.available_tasks()

            else:
                print(f"\n[ERROR] Unknown task command: {subcmd}\n")

            return

        # Workspace hygiene and health
        if cmd == "workspace":
            from core.workspace_manager import WorkspaceCoordinator

            wc = WorkspaceCoordinator()

            if len(sys.argv) < 3:
                print("\n🧹 Workspace Management\n")
                print("Available commands:")
                print("  report     - Generate workspace health report")
                print("  defrag     - Consolidate build outputs and docs")
                print("  cleanup    - Remove duplicates and temp files")
                print("  diagnose   - Capture diagnostic pack\n")
                print("Usage: python hub.py workspace <command>\n")
                return

            subcmd = sys.argv[2].lower()

            if subcmd == "report":
                report = wc.generate_workspace_report()
                print("\n--- WORKSPACE HEALTH REPORT ---")
                print(f"Health Score: {report['health_score']}")
                print(
                    f"Duplicates:   {report['duplicates']['redundant_files']} files ({report['duplicates']['wasted_space_mb']} MB)"
                )
                print(
                    f"Temp Files:   {report['temp_files']['count']} files ({report['temp_files']['wasted_space_mb']} MB)"
                )
                print(f"Large Files:  {report['large_files']['count']} (>50MB)")
                print(
                    f"Runaway Bot:  {'YES' if report['runaway_bot_check']['is_runaway'] else 'No'}"
                )
                print("-" * 30 + "\n")
                wc.save_report(report)

            elif subcmd == "defrag":
                results = wc.defrag_workspace(dry_run=False)
                print("\n✓ Defragmentation complete:")
                for r in results:
                    print(f"  - {r}")
                print()

            elif subcmd == "cleanup":
                deleted_dupes = wc.cleanup_duplicates(dry_run=False)
                deleted_temp = wc.cleanup_temp_files(dry_run=False)
                print("\n✓ Cleanup complete:")
                print(f"  - Removed {len(deleted_dupes)} duplicate files")
                print(f"  - Removed {len(deleted_temp)} temporary files\n")

            elif subcmd == "diagnose":
                path = wc.capture_diagnostic_pack()
                print(f"\n✓ Diagnostic pack captured: {path}\n")

            elif subcmd == "audit":
                print("\n🔍 Running AI-Readiness Audit...")
                from core.batch_gen import TaskGenerator

                # Mocking dependencies for audit
                tg = TaskGenerator(None, None, wc)
                suggestions = await tg.suggest_improvements()
                ai_tasks = [s for s in suggestions if s.get("type") == "ai_readiness"]

                if ai_tasks:
                    print(f"Found {len(ai_tasks)} AI-readiness gaps:")
                    for task in ai_tasks:
                        print(f"  - {task['title']}")
                        print(f"    {task['description']}")
                else:
                    print("✓ No AI-readiness gaps found!")
                print()

            elif subcmd == "patch":
                if len(sys.argv) < 4:
                    print("\nUsage: python hub.py workspace patch <module_name>\n")
                    return
                module_name = sys.argv[3]
                if hub.patch.reload_module(module_name):
                    print(f"\n✓ Successfully patched module: {module_name}\n")
                else:
                    print(f"\n❌ Failed to patch module: {module_name}\n")

            else:
                print(f"\n❌ Unknown workspace command: {subcmd}\n")

            return

        # Game Mode management
        if cmd == "game":
            if len(sys.argv) < 3:
                print("\n🎮 Game Mode Management\n")
                print("Available commands:")
                print(
                    "  enter        - Activate game mode (starts Maelstrom + trainers)"
                )
                print("  exit         - Deactivate game mode (graceful shutdown)")
                print("  toggle       - Toggle game mode on/off")
                print("  status       - Show current game mode status")
                print("  configure    - Show/set game mode configuration\n")
                print("Usage: python hub.py game <command>\n")
                return

            subcmd = sys.argv[2].lower()

            if subcmd == "enter":
                print("\n🎮 Entering Game Mode...")
                success = await hub.game_mode.enter()
                if success:
                    print("✓ Game Mode ACTIVE")
                    status = hub.game_mode.get_status()
                    if status.get("session"):
                        print(
                            f"  Session started: {status['session'].get('started_at', 'now')}"
                        )
                    print("  Maelstrom: starting...")
                    print("  Trainers: enabled\n")
                else:
                    state = hub.game_mode.get_status().get("state", "UNKNOWN")
                    print(f"❌ Failed to enter game mode (current state: {state})\n")

            elif subcmd == "exit":
                print("\n🎮 Exiting Game Mode...")
                success = await hub.game_mode.exit()
                if success:
                    print("✓ Game Mode INACTIVE")
                    print("  Maelstrom: stopped")
                    print("  Trainers: disabled\n")
                else:
                    state = hub.game_mode.get_status().get("state", "UNKNOWN")
                    print(f"❌ Failed to exit game mode (current state: {state})\n")

            elif subcmd == "toggle":
                status = hub.game_mode.get_status()
                current = status.get("state", "INACTIVE")
                print(f"\n🎮 Toggling Game Mode (current: {current})...")
                success = await hub.game_mode.toggle()
                new_status = hub.game_mode.get_status()
                new_state = new_status.get("state", "UNKNOWN")
                print(f"✓ Game Mode now: {new_state}\n")

            elif subcmd == "status":
                status = hub.game_mode.get_status()
                state = status.get("state", "INACTIVE")
                config = status.get("config", {})
                session = status.get("session")

                idle_mode = config.get("idle_mode", "automation_aware")
                idle_timeout = config.get("idle_timeout_minutes", 30)
                timeout_str = (
                    f"{idle_timeout} min ({idle_mode})"
                    if idle_timeout > 0
                    else "disabled"
                )

                print("\n🎮 GAME MODE STATUS")
                print("=" * 50)
                print(f"State:          {state}")
                print(f"Idle Timeout:   {timeout_str}")
                print(
                    f"Auto-detect:    {'Yes' if config.get('auto_detect_game') else 'No'}"
                )
                print(
                    f"Start Maelstrom:{' Yes' if config.get('start_maelstrom', True) else ' No'}"
                )

                if session:
                    print("-" * 50)
                    print(f"Session Start:  {session.get('started_at', 'Unknown')}")
                    print(
                        f"Duration:       {session.get('duration_minutes', 0):.1f} min"
                    )
                    print(
                        f"Human Idle:     {session.get('human_idle_minutes', 0):.1f} min"
                    )
                    print(
                        f"Any Idle:       {session.get('automation_idle_minutes', 0):.1f} min"
                    )
                    print(f"Commands Exec:  {session.get('commands_executed', 0)}")
                    print(f"Trainer Cycles: {session.get('trainer_cycles', 0)}")
                    print(f"Game Events:    {session.get('game_events', 0)}")
                    print(
                        f"Trainers Used:  {', '.join(session.get('trainers_started', [])) or 'None'}"
                    )
                print("=" * 50 + "\n")

            elif subcmd == "configure":
                if len(sys.argv) < 4:
                    print("\nUsage: python hub.py game configure <key> [value]")
                    print("\nConfigurable keys:")
                    print(
                        "  idle_timeout_minutes     - Minutes before auto-exit (0 = disabled)"
                    )
                    print("  idle_mode                - What counts as activity:")
                    print(
                        "                             human_only | automation_aware | never"
                    )
                    print("  auto_detect_game         - true/false")
                    print("  start_maelstrom          - true/false")
                    print("  enable_trainers          - true/false")
                    print(
                        "  count_trainer_cycles     - true/false (automation_aware mode)"
                    )
                    print(
                        "  count_maelstrom_commands - true/false (automation_aware mode)"
                    )
                    print(
                        "  count_game_events        - true/false (automation_aware mode)\n"
                    )
                    return

                key = sys.argv[3]
                value = sys.argv[4] if len(sys.argv) > 4 else None

                if value is None:
                    current = getattr(hub.game_mode.config, key, "Not found")
                    print(f"\n{key} = {current}\n")
                else:
                    # Parse value
                    if value.lower() in {"true", "yes", "1"}:
                        parsed = True
                    elif value.lower() in {"false", "no", "0"}:
                        parsed = False
                    else:
                        try:
                            parsed = int(value)
                        except ValueError:
                            parsed = value

                    hub.game_mode.configure(**{key: parsed})
                    print(f"\n✓ Set {key} = {parsed}\n")

            else:
                print(f"\n❌ Unknown game command: {subcmd}\n")

            return

        # Batch operations (50% cost savings)
        if cmd == "batch":
            if not hub.batch_manager:
                print("\n❌ Batch API not configured - set OPENAI_API_KEY in .env\n")
                return

            if len(sys.argv) < 3:
                print("\n🚀 Batch Operations (50% Cost Savings, ≤24h Completion)\n")
                print("Available commands:")
                print(
                    "  submit [max]   - Submit eligible tasks (default: 50, use aggressively!)"
                )
                print("  status         - List all active batches")
                print("  check <id>     - Check specific batch status")
                print("  task <id>      - Batch a single task\n")
                print(
                    "💡 Best Practice: Batch aggressively - all tasks complete within 24 hours\n"
                )
                print("Usage: python hub.py batch <command>\n")
                return

            subcmd = sys.argv[2].lower()

            if subcmd == "submit":
                max_tasks = int(sys.argv[3]) if len(sys.argv) > 3 else 50
                unbatched = hub.tasks.find_unbatched_tasks(max_count=max_tasks)

                if not unbatched:
                    print("\n[!] No eligible tasks for batching\n")
                    return

                print(f"\n[*] Found {len(unbatched)} unbatched tasks")
                batch_id = await hub.tasks.batch_multiple_tasks(max_tasks=max_tasks)

                if batch_id:
                    print(f"\n✅ Batch submitted: {batch_id}")
                    print(f"   Tasks: {len(unbatched)}")
                    print("   Cost savings: ~50%\n")
                else:
                    print("\n❌ Batch submission failed\n")

            elif subcmd == "status":
                active = hub.batch_manager.list_active_batches()
                if not active:
                    print("\n[!] No active batches\n")
                    return

                print(f"\nACTIVE BATCHES ({len(active)})")
                print("-" * 80)
                for b in active:
                    print(f"ID:     {b['id']}")
                    print(f"Status: {b['status']}")
                    if b.get("metadata"):
                        print(f"Meta:   {b['metadata']}")
                    print("-" * 80)
                print()

            elif subcmd == "check":
                if len(sys.argv) < 4:
                    print("\nUsage: python hub.py batch check <batch_id>\n")
                    return

                batch_id = sys.argv[3]
                try:
                    status = hub.batch_manager.get_batch_status(batch_id)
                    print(f"\nBATCH STATUS: {batch_id}")
                    print("=" * 80)
                    print(f"Status:    {status['status']}")
                    print(f"Total:     {status['request_counts']['total']}")
                    print(f"Completed: {status['request_counts']['completed']}")
                    print(f"Failed:    {status['request_counts']['failed']}")
                    print("=" * 80 + "\n")
                except Exception as e:
                    print(f"\n❌ Error: {e}\n")

            elif subcmd == "task":
                if len(sys.argv) < 4:
                    print("\nUsage: python hub.py batch task <task_id>\n")
                    return
                task_id = sys.argv[3]
                batch_id = await hub.tasks.batch_task(task_id)
                if batch_id:
                    print(f"\n✓ Batch submitted: {batch_id}\n")
                else:
                    print(f"\n❌ Failed to batch task {task_id}\n")

            elif subcmd == "multiple":
                batch_id = await hub.tasks.batch_multiple_tasks()
                if batch_id:
                    print(f"\n✓ Batch submitted: {batch_id}\n")
                else:
                    print("\n❌ No tasks available to batch or batching failed\n")

            else:
                print(f"\n❌ Unknown batch command: {subcmd}\n")

            return

        # Legacy commands (maintained for backward compatibility)
        if cmd == "claim":
            actor = sys.argv[2] if len(sys.argv) > 2 else "Sixth"
            task = hub.tasks.claim_task(actor_name=actor)
            if task:
                print(f"\n--- TASK CLAIMED BY {actor.upper()} ---")
                print(f"ID: {task['id']}")
                print(f"Title: {task['title']}")
                print(f"Artifacts: artifacts/guild/{task['id']}/")
                print("-----------------------------------\n")
            else:
                print("\nNo queued tasks found on the board.\n")
            return
        elif cmd == "complete":
            if len(sys.argv) < 3:
                print("\nUsage: python hub.py complete [TaskID]\n")
                return
            task_id = sys.argv[2]
            if hub.tasks.complete_task(task_id):
                print(f"\nTask {task_id} marked as Done.\n")
            else:
                print(f"\nTask {task_id} not found or already completed.\n")
            return
        elif cmd == "board":
            if not hub.tasks.guild:
                print("\n[ERROR] Guild board not available\n")
                return
            _, tasks, status_map = hub.tasks.guild.parse_board()

            # Filter for claimed but uncompleted tasks (In Progress)
            active_tasks = [t for t in tasks if t["status"] == "In Progress"]

            # Priority mapping for sorting
            priority_order = {"High": 0, "Medium": 1, "Low": 2}
            active_tasks.sort(key=lambda x: priority_order.get(x["priority"], 3))

            print("\n--- AAS ACTIVE TASK BOARD (In Progress) ---")

            if not active_tasks:
                print("\n[!] No tasks currently in progress.\n")
            else:
                current_priority = None
                for t in active_tasks:
                    if t["priority"] != current_priority:
                        current_priority = t["priority"]
                        print(f"\n[{current_priority.upper()} PRIORITY]")
                        print("-" * 80)
                        print(f"{'ID':<10} | {'Assignee':<12} | {'Title'}")
                        print("-" * 80)

                    assignee = t.get("assignee", "Unassigned")
                    print(f"{t['id']:<10} | {assignee:<12} | {t['title'][:60]}")

            print("\n" + "=" * 80)
            # Show summary statistics
            done = sum(1 for t in tasks if t["status"] == "Done")
            in_progress = len(active_tasks)
            queued = sum(1 for t in tasks if t["status"] == "queued")
            blocked_tasks = hub.tasks.guild.get_blocked_tasks()
            blocked_count = len(blocked_tasks)

            print(
                f" Summary: {done} Done | {in_progress} In Progress | {queued} Queued | {blocked_count} Blocked"
            )

            if blocked_tasks:
                print(f"\n Blocked Tasks ({blocked_count}):")
                for bt in blocked_tasks[:5]:  # Show first 5
                    print(
                        f"   - {bt['id']} waiting on {', '.join(bt['blocking_tasks'])}"
                    )
                if len(blocked_tasks) > 5:
                    print(f"   ... and {len(blocked_tasks) - 5} more")

            print()
            return
        elif cmd == "blocked":
            if not hub.tasks.guild:
                print("\n[ERROR] Guild board not available\n")
                return
            blocked_tasks = hub.tasks.guild.get_blocked_tasks()

            if not blocked_tasks:
                print("\n[OK] No blocked tasks! All dependencies are satisfied.\n")
                return

            print(f"\n BLOCKED TASKS ({len(blocked_tasks)})")
            print("-" * 80)

            for bt in blocked_tasks:
                blocking = ", ".join(bt["blocking_tasks"])
                print(f"\n{bt['id']} [{bt['priority'].upper()}]: {bt['title']}")
                print(f"   Waiting on: {blocking}")

            print("\n" + "-" * 80)
            print(f"Total: {len(blocked_tasks)} tasks blocked\n")
            return

    # 4. Start IPC, gRPC and Web Servers
    ipc_ports = resolved_ipc_ports
    ipc_task = asyncio.create_task(
        serve_ipc(port=config.ipc_port, service=hub.ipc, ports=ipc_ports)
    )

    grpc_port = int(os.getenv("AAS_GRPC_PORT", "50052"))
    grpc_server = serve_grpc(hub, port=grpc_port)

    # Start FastAPI in a separate thread or as a task
    app = create_app(hub)
    web_config = uvicorn.Config(app, host=web_host, port=web_port, log_level="info")
    web_server = uvicorn.Server(web_config)

    # 5. Start background batch monitor (always running, checks config dynamically)
    batch_monitor_task = None
    if hub.batch_manager:

        async def run_batch_monitor():
            """Background task to monitor and auto-submit batch jobs (checks config on each iteration)."""
            logger.info(
                "Starting background batch monitor (config-driven intervals, toggle-enabled)"
            )
            error_backoff = 60
            while True:
                try:
                    # Check if auto-monitor is enabled (allows runtime toggling)
                    if not hub.config.batch_auto_monitor:
                        await asyncio.sleep(10)
                        continue

                    interval = max(
                        5, int(getattr(hub.config, "batch_monitor_scan_interval", 60))
                    )
                    active_batches = []
                    with contextlib.suppress(Exception):
                        active_batches = hub.batch_manager.list_active_batches()

                    # When batches exist, use the tighter check interval if configured
                    if active_batches:
                        interval = min(
                            interval,
                            max(
                                5,
                                int(
                                    getattr(
                                        hub.config,
                                        "batch_monitor_check_interval",
                                        interval,
                                    )
                                ),
                            ),
                        )

                    # Find eligible unbatched tasks (scan up to 50)
                    max_tasks = max(
                        1, int(getattr(hub.config, "batch_monitor_max_tasks", 50))
                    )
                    min_tasks = max(
                        1, int(getattr(hub.config, "batch_monitor_min_tasks", 3))
                    )
                    unbatched = hub.tasks.find_unbatched_tasks(max_count=max_tasks)

                    if len(unbatched) >= min_tasks:  # Batch when threshold is met
                        logger.info(
                            f"Found {len(unbatched)} unbatched tasks - auto-submitting (≤24h completion)"
                        )
                        batch_id = await hub.tasks.batch_multiple_tasks(
                            max_tasks=max_tasks
                        )
                        if batch_id:
                            logger.success(
                                f"Auto-submitted batch: {batch_id} ({len(unbatched)} tasks)"
                            )
                        error_backoff = 60  # reset after success

                    await asyncio.sleep(interval)
                except Exception as e:
                    logger.error(f"Batch monitor error: {e}")
                    # Back off to avoid log spam when API rejects (e.g., archived project / 401)
                    await asyncio.sleep(error_backoff)
                    error_backoff = min(error_backoff * 2, 600)

        batch_monitor_task = asyncio.create_task(run_batch_monitor())

    # 6. Health/agent broadcaster for WebSocket clients (push vs. polling)
    async def run_ws_broadcaster():
        last_health_hash = None
        last_agents_hash = None
        while True:
            try:
                await asyncio.sleep(15)
                if not hub.ws:
                    continue
                health = hub.get_health_summary()
                agents = hub.collaboration.get_active_agents()
                # Hash payloads to avoid spam
                h_bytes = json.dumps(health, sort_keys=True).encode()
                a_bytes = json.dumps(agents, sort_keys=True).encode()
                health_hash = hashlib.sha256(h_bytes).hexdigest()
                agents_hash = hashlib.sha256(a_bytes).hexdigest()
                if health_hash != last_health_hash:
                    last_health_hash = health_hash
                    await hub.ws.broadcast(
                        {"event_type": "HEALTH_UPDATE", "payload": health}
                    )
                if agents_hash != last_agents_hash:
                    last_agents_hash = agents_hash
                    await hub.ws.broadcast(
                        {"event_type": "AGENT_UPDATE", "payload": agents}
                    )
            except asyncio.CancelledError:
                break
            except Exception as e:
                logger.debug(f"WS broadcaster error: {e}")
        logger.info("WS broadcaster stopped")

    ws_broadcast_task = asyncio.create_task(run_ws_broadcaster())

    # 7. GitHub poller + OpenAI reconcile (if configured)
    async def run_github_loop():
        if not getattr(hub, "github", None):
            return
        poll_interval = int(os.getenv("GITHUB_POLL_INTERVAL_SECONDS", "300"))
        owner = os.getenv("GITHUB_OWNER")
        repo = os.getenv("GITHUB_REPO")
        token = os.getenv("GITHUB_TOKEN")
        branch = os.getenv("GITHUB_BRANCH", "main")
        api_key = os.getenv("OPENAI_API_KEY")
        model = os.getenv("OPENAI_MODEL", "gpt-4.1")
        while True:
            try:
                # Poll GitHub if enabled
                if (
                    owner
                    and repo
                    and _is_automation_enabled(hub.github, "github.poller")
                ):
                    await hub.github.poll_and_enqueue(owner, repo, token, branch)
                # Submit queued jobs to OpenAI if automation enabled
                if api_key and _is_automation_enabled(hub.github, "openai.analysis"):
                    await hub.github.submit_openai_jobs(api_key=api_key, model=model)
                    await hub.github.reconcile_openai(api_key=api_key)
            except Exception as e:
                logger.debug(f"GitHub loop error: {e}")
            await asyncio.sleep(min(60, poll_interval))

    def _is_automation_enabled(github_integration, automation_id: str) -> bool:
        try:
            with github_integration._connect() as conn:
                row = conn.execute(
                    "SELECT enabled FROM automations WHERE id=?", (automation_id,)
                ).fetchone()
                return bool(row and row[0])
        except Exception:
            return False

    github_task = asyncio.create_task(run_github_loop())

    # 8. Game Mode idle timeout monitor
    async def run_game_mode_monitor():
        """Background task to check game mode idle timeout."""
        logger.debug("Game Mode monitor started")
        while True:
            try:
                await asyncio.sleep(60)  # Check every minute
                if hub.game_mode._state.name == "ACTIVE":
                    await hub.game_mode._check_idle_timeout()
            except asyncio.CancelledError:
                break
            except Exception as e:
                logger.debug(f"Game mode monitor error: {e}")
        logger.debug("Game Mode monitor stopped")

    game_mode_task = asyncio.create_task(run_game_mode_monitor())

    logger.success(
        f"AAS Hub is now running (IPC candidates: {ipc_ports}, Web: {web_host}:{web_port})"
    )
    if batch_monitor_task:
        status = "ENABLED" if config.batch_auto_monitor else "DISABLED"
        logger.info(
            f"Batch auto-monitor: {status} (aggressive batching, ≤24h completion, runtime toggle)"
        )

    try:
        tasks = [
            ipc_task,
            web_server.serve(),
            ws_broadcast_task,
            github_task,
            game_mode_task,
        ]
        if batch_monitor_task:
            tasks.append(batch_monitor_task)
        await asyncio.gather(*tasks)
    except asyncio.CancelledError:
        logger.info("AAS Hub shutting down...")
        if batch_monitor_task:
            batch_monitor_task.cancel()
        ws_broadcast_task.cancel()
        github_task.cancel()
        game_mode_task.cancel()
        # Gracefully exit game mode if active
        if hub.game_mode._state.name == "ACTIVE":
            logger.info("Exiting Game Mode before shutdown...")
            await hub.game_mode.exit()
    finally:
        if "pid_file" in locals():
            try:
                current_pid = str(os.getpid())
                if (
                    pid_file.exists()
                    and pid_file.read_text(encoding="utf-8").strip() == current_pid
                ):
                    pid_file.unlink()
                    logger.debug("Removed PID file on shutdown")
            except Exception as e:
                logger.warning(f"Failed to clean up PID file: {e}")


if __name__ == "__main__":
    asyncio.run(main())

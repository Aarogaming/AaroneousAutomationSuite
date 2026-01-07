import asyncio
import sys
import argparse
import uvicorn
import os
import threading
import webbrowser
from loguru import logger
from typing import Optional
from pathlib import Path
from core.config import load_config
from core.ipc_server import serve_ipc
from core.web_server import create_app
from core.preflight import run_preflight
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
    
    def create_task(self, title: str, priority: str = "Medium", depends: Optional[str] = None, description: Optional[str] = None):
        """Create a new task"""
        new_id = self.task_manager.add_task(
            priority=priority,
            title=title,
            description=description or title,
            depends_on=depends or "-"
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
        print(f"     Artifacts: artifacts/handoff/{task_id}/\n")
        return True
    
    def complete_task(self, task_id: str):
        """Mark task as complete"""
        return self.task_manager.complete_task(task_id)
    
    def list_tasks(self, status: Optional[str] = None, priority: Optional[str] = None, assignee: Optional[str] = None):
        """List tasks with optional filters"""
        if not self.task_manager.handoff:
            print("\n[ERROR] Handoff board not available\n")
            return
            
        _, tasks, _ = self.task_manager.handoff.parse_board()
        
        # Apply filters
        filtered = tasks
        if status:
            filtered = [t for t in filtered if t['status'].lower() == status.lower()]
        if priority:
            filtered = [t for t in filtered if t['priority'].lower() == priority.lower()]
        if assignee:
            filtered = [t for t in filtered if t.get('assignee', '-').lower() == assignee.lower()]
        
        if not filtered:
            print("\n[!] No tasks match the filters\n")
            return
        
        print(f"\nTASKS ({len(filtered)} found)")
        print("-" * 100)
        print(f"{'ID':<12} | {'Priority':<10} | {'Status':<14} | {'Assignee':<12} | {'Title'}")
        print("-" * 100)
        
        for t in filtered:
            assignee_display = t.get('assignee', '-')
            print(f"{t['id']:<12} | {t['priority']:<10} | {t['status']:<14} | {assignee_display:<12} | {t['title'][:50]}")
        
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
        
        print(f"\nNEXT AVAILABLE TASK")
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
        img = Image.new('RGBA', (size, size), color=(0, 0, 0, 0))
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
        draw.polygon([(peak_x, top), left_bottom, right_bottom], fill='white')
        inner_offset = int(size * 0.12)
        draw.polygon([
            (peak_x, top + int(inner_offset * 1.5)),
            (left_bottom[0] + inner_offset, left_bottom[1] - inner_offset),
            (right_bottom[0] - inner_offset, right_bottom[1] - inner_offset)
        ], fill=(67, 56, 202))
        bar_y = top + int(letter_height * 0.6)
        bar_thickness = int(size * 0.08)
        bar_left = left + int(letter_width * 0.25)
        bar_right = left + int(letter_width * 0.75)
        draw.rectangle([bar_left, bar_y, bar_right, bar_y + bar_thickness], fill='white')
        return img

    def start_inline_tray(loop: asyncio.AbstractEventLoop):
        """Start tray UI in a background thread within the same process."""
        if pystray is None:
            logger.warning("Tray UI unavailable (missing pystray/Pillow); continuing without tray UI.")
            return None
        if os.getenv("WSL_DISTRO_NAME"):
            logger.info("Tray skipped: WSL environment detected (no native system tray).")
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
            pystray.MenuItem("Quit Hub", quit_hub)
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
    log_file.parent.mkdir(parents=True, exist_ok=True)
    logger.remove()
    log_format = "{time:YYYY-MM-DD HH:mm:ss} | {level:<8} | {message}"
    logger.add(sys.stderr, level="INFO", format=log_format, enqueue=True)
    logger.add(log_file, rotation="10 MB", retention="10 days", level="DEBUG", format=log_format, enqueue=True)
    
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
    preflight = run_preflight(config=config, workspace_root=Path.cwd(), web_host=web_host, web_port=web_port)
    preflight.log()
    if preflight.needs_reexec and preflight.preferred_python and not os.getenv("AAS_PREFLIGHT_REEXEC"):
        try:
            new_env = os.environ.copy()
            new_env["AAS_PREFLIGHT_REEXEC"] = "1"
            python_path = str(preflight.preferred_python)
            logger.info(f"Re-launching Hub with workspace Python at {python_path}")
            os.execve(python_path, [python_path] + sys.argv, new_env)
        except Exception as e:
            logger.warning(f"Preflight re-launch with workspace Python failed, continuing: {e}")
    if preflight.issues:
        logger.critical("Startup blocked by preflight issues; resolve above and retry.")
        return
    web_host = preflight.web_host
    web_port = preflight.web_port
    config.ipc_port = preflight.ipc_port
    resolved_ipc_ports = preflight.ipc_ports

    # 1b. Write PID file for unified start/stop tooling
    pid_file = Path("artifacts/hub.pid")
    try:
        pid_file.write_text(str(os.getpid()), encoding="utf-8")
        logger.debug(f"Wrote PID file to {pid_file}")
    except Exception as e:
        logger.warning(f"Failed to write PID file: {e}")

    # 2. Initialize Manager Hub (Unified access to all managers)
    from core.managers import ManagerHub
    hub = ManagerHub.create(config=config)
    
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
                print("  create <title> [--priority High] [--depends AAS-001,AAS-002] [--description 'text']")
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
                    print("\nUsage: python hub.py task create <title> [--priority High] [--depends AAS-001]\n")
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
                print(f"\n--- WORKSPACE HEALTH REPORT ---")
                print(f"Health Score: {report['health_score']}")
                print(f"Duplicates:   {report['duplicates']['redundant_files']} files ({report['duplicates']['wasted_space_mb']} MB)")
                print(f"Temp Files:   {report['temp_files']['count']} files ({report['temp_files']['wasted_space_mb']} MB)")
                print(f"Large Files:  {report['large_files']['count']} (>50MB)")
                print(f"Runaway Bot:  {'YES' if report['runaway_bot_check']['is_runaway'] else 'No'}")
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
                print(f"\n✓ Cleanup complete:")
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
                ai_tasks = [s for s in suggestions if s.get('type') == 'ai_readiness']
                
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
        
        # Batch operations (50% cost savings)
        if cmd == "batch":
            if not hub.batch_manager:
                print("\n❌ Batch API not configured - set OPENAI_API_KEY in .env\n")
                return
            
            if len(sys.argv) < 3:
                print("\n🚀 Batch Operations (50% Cost Savings, ≤24h Completion)\n")
                print("Available commands:")
                print("  submit [max]   - Submit eligible tasks (default: 50, use aggressively!)")
                print("  status         - List all active batches")
                print("  check <id>     - Check specific batch status")
                print("  task <id>      - Batch a single task\n")
                print("💡 Best Practice: Batch aggressively - all tasks complete within 24 hours\n")
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
                    print(f"   Cost savings: ~50%\n")
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
                    if b.get('metadata'):
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
                    print(f"\n❌ No tasks available to batch or batching failed\n")
            
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
                print(f"Artifacts: artifacts/handoff/{task['id']}/")
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
            if not hub.tasks.handoff:
                print("\n[ERROR] Handoff board not available\n")
                return
            _, tasks, status_map = hub.tasks.handoff.parse_board()
            
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
                    
                    assignee = t.get('assignee', 'Unassigned')
                    print(f"{t['id']:<10} | {assignee:<12} | {t['title'][:60]}")
            
            print("\n" + "=" * 80)
            # Show summary statistics
            done = sum(1 for t in tasks if t["status"] == "Done")
            in_progress = len(active_tasks)
            queued = sum(1 for t in tasks if t["status"] == "queued")
            blocked_tasks = hub.tasks.handoff.get_blocked_tasks()
            blocked_count = len(blocked_tasks)
            
            print(f" Summary: {done} Done | {in_progress} In Progress | {queued} Queued | {blocked_count} Blocked")
            
            if blocked_tasks:
                print(f"\n Blocked Tasks ({blocked_count}):")
                for bt in blocked_tasks[:5]:  # Show first 5
                    print(f"   - {bt['id']} waiting on {', '.join(bt['blocking_tasks'])}")
                if len(blocked_tasks) > 5:
                    print(f"   ... and {len(blocked_tasks) - 5} more")
            
            print()
            return
        elif cmd == "blocked":
            if not hub.tasks.handoff:
                print("\n[ERROR] Handoff board not available\n")
                return
            blocked_tasks = hub.tasks.handoff.get_blocked_tasks()
            
            if not blocked_tasks:
                print("\n[OK] No blocked tasks! All dependencies are satisfied.\n")
                return
            
            print(f"\n BLOCKED TASKS ({len(blocked_tasks)})")
            print("-" * 80)
            
            for bt in blocked_tasks:
                blocking = ", ".join(bt['blocking_tasks'])
                print(f"\n{bt['id']} [{bt['priority'].upper()}]: {bt['title']}")
                print(f"   Waiting on: {blocking}")
            
            print("\n" + "-" * 80)
            print(f"Total: {len(blocked_tasks)} tasks blocked\n")
            return

    # 4. Start IPC and Web Servers
    ipc_ports = resolved_ipc_ports
    ipc_task = asyncio.create_task(serve_ipc(port=config.ipc_port, service=hub.ipc, ports=ipc_ports))
    
    # Start FastAPI in a separate thread or as a task
    app = create_app(hub)
    web_config = uvicorn.Config(app, host=web_host, port=web_port, log_level="info")
    web_server = uvicorn.Server(web_config)
    
    # 5. Start background batch monitor (always running, checks config dynamically)
    batch_monitor_task = None
    if hub.batch_manager:
        async def run_batch_monitor():
            """Background task to monitor and auto-submit batch jobs (checks config on each iteration)."""
            logger.info("Starting background batch monitor (60s scan interval, toggle-enabled)")
            while True:
                try:
                    await asyncio.sleep(60)  # Check every minute
                    
                    # Check if auto-monitor is enabled (allows runtime toggling)
                    if not hub.config.batch_auto_monitor:
                        continue
                    
                    # Find eligible unbatched tasks (scan up to 50)
                    unbatched = hub.tasks.find_unbatched_tasks(max_count=50)
                    if len(unbatched) >= 3:  # Batch aggressively when 3+ tasks available
                        logger.info(f"Found {len(unbatched)} unbatched tasks - auto-submitting (≤24h completion)")
                        batch_id = await hub.tasks.batch_multiple_tasks(max_tasks=50)
                        if batch_id:
                            logger.success(f"Auto-submitted batch: {batch_id} ({len(unbatched)} tasks)")
                except Exception as e:
                    logger.error(f"Batch monitor error: {e}")
        
        batch_monitor_task = asyncio.create_task(run_batch_monitor())
    
    logger.success(f"AAS Hub is now running (IPC candidates: {ipc_ports}, Web: {web_host}:{web_port})")
    if batch_monitor_task:
        status = "ENABLED" if config.batch_auto_monitor else "DISABLED"
        logger.info(f"Batch auto-monitor: {status} (aggressive batching, ≤24h completion, runtime toggle)")

    
    try:
        tasks = [ipc_task, web_server.serve()]
        if batch_monitor_task:
            tasks.append(batch_monitor_task)
        await asyncio.gather(*tasks)
    except asyncio.CancelledError:
        logger.info("AAS Hub shutting down...")
        if batch_monitor_task:
            batch_monitor_task.cancel()
    finally:
        if 'pid_file' in locals():
            try:
                current_pid = str(os.getpid())
                if pid_file.exists() and pid_file.read_text(encoding="utf-8").strip() == current_pid:
                    pid_file.unlink()
                    logger.debug("Removed PID file on shutdown")
            except Exception as e:
                logger.warning(f"Failed to clean up PID file: {e}")

if __name__ == "__main__":
    asyncio.run(main())

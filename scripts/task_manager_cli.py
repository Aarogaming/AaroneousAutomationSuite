"""
Task Manager CLI - Unified interface for task management

Usage:
    python scripts/task_manager_cli.py list-unbatched
    python scripts/task_manager_cli.py find-next
    python scripts/task_manager_cli.py claim [task_id]
    python scripts/task_manager_cli.py status <task_id>
    python scripts/task_manager_cli.py batch <task_id>
    python scripts/task_manager_cli.py batch-all [--max N]
    python scripts/task_manager_cli.py health
    python scripts/task_manager_cli.py workspace-scan
    python scripts/task_manager_cli.py workspace-duplicates
    python scripts/task_manager_cli.py workspace-cleanup [--dry-run]
    python scripts/task_manager_cli.py workspace-report
    python scripts/task_manager_cli.py detect-runaway
    python scripts/task_manager_cli.py workspace-defrag [--dry-run]
    python scripts/task_manager_cli.py heartbeat [--client-id ID]
    python scripts/task_manager_cli.py subscribe [--client-id ID]
    python scripts/task_manager_cli.py docs-generate
    python scripts/task_manager_cli.py decompose --goal "GOAL" [--priority PRIORITY] [--type TYPE]
    python scripts/task_manager_cli.py devtoys [task_name] [--text TEXT] [--pattern PATTERN]
    python scripts/task_manager_cli.py ngrok [start|stop|status] [--port PORT]
"""

import asyncio
import socket
import platform
import sys
from datetime import datetime
from pathlib import Path

# Add parent directory to path
sys.path.insert(0, str(Path(__file__).parent.parent))

from loguru import logger
from core.task_manager import TaskManager
from core.config import AASConfig


def print_task(task: dict, include_batch_status: bool = False):
    """Pretty print a task."""
    print(f"\n{'='*60}")
    print(f"ID: {task['id']}")
    print(f"Title: {task['title']}")
    print(f"Priority: {task['priority']}")
    print(f"Status: {task.get('status', 'N/A')}")
    print(f"Assignee: {task.get('assignee', 'N/A')}")
    print(f"Dependencies: {task.get('depends_on', 'N/A')}")
    
    if include_batch_status:
        print(f"Batched: {task.get('batched', False)}")
        if task.get('batched'):
            print(f"Batch ID: {task.get('batch_id', 'N/A')}")
    
    print('='*60)


async def list_unbatched(tm: TaskManager, max_count: int = 10):
    """List tasks that haven't been batched."""
    unbatched = tm.find_unbatched_tasks(max_count=max_count)
    
    if not unbatched:
        print("\n✅ No unbatched tasks found (all eligible tasks have been batched)")
        return
    
    print(f"\n📋 Found {len(unbatched)} unbatched tasks:\n")
    for task in unbatched:
        print(f"  • {task['id']} [{task['priority'].upper()}]: {task['title']}")
        if task['depends_on'] and task['depends_on'] != '-':
            print(f"    Dependencies: {task['depends_on']}")


async def find_next(tm: TaskManager):
    """Find the next claimable task."""
    task = tm.find_next_claimable_task(exclude_batched=False)
    
    if not task:
        print("\n❌ No claimable tasks found")
        return
    
    print("\n🎯 Next claimable task:")
    print_task(task)
    
    # Check if it's been batched
    is_batched = tm._is_task_batched(task['id'])
    if is_batched:
        print("\n⚠️  Note: This task has been batched for planning")


async def claim_task(tm: TaskManager, task_id: str | None = None):
    """Claim a task."""
    claimed = tm.claim_task(task_id=task_id, actor_name="GitHub Copilot")
    
    if not claimed:
        print(f"\n❌ Failed to claim task{' ' + task_id if task_id else ''}")
        return None
    
    print(f"\n✅ Successfully claimed task:")
    print_task(claimed)
    
    return claimed


async def task_status(tm: TaskManager, task_id: str):
    """Get task status."""
    status = tm.get_task_status(task_id)
    
    if 'error' in status:
        print(f"\n❌ {status['error']}")
        return
    
    print_task(status, include_batch_status=True)


async def add_task(tm: TaskManager, priority: str, title: str, description: str, task_type: str = "feature", depends_on: str = "-"):
    """Add a new task."""
    task_id = tm.add_task(priority, title, description, depends_on, task_type)
    print(f"\n✅ Successfully added task {task_id}")
    return task_id


async def complete_task(tm: TaskManager, task_id: str):
    """Complete a task."""
    success = tm.complete_task(task_id)
    if success:
        print(f"\n✅ Successfully completed task {task_id}")
    else:
        print(f"\n❌ Failed to complete task {task_id}")
    return success


async def decompose_goal(tm: TaskManager, goal: str, priority: str = "medium", task_type: str = "feature"):
    """Decompose a goal into sub-tasks."""
    print(f"\n🧠 Decomposing goal: {goal}...")
    task_ids = await tm.decompose_and_add_tasks(goal, priority, task_type)
    print(f"✅ Successfully created {len(task_ids)} sub-tasks: {', '.join(task_ids)}")
    return task_ids


async def batch_task(tm: TaskManager, task_id: str):
    """Batch a specific task."""
    print(f"\n⏳ Submitting {task_id} for batch processing...")
    
    batch_id = await tm.batch_task(task_id)
    
    if batch_id:
        print(f"✅ Task {task_id} batched successfully: {batch_id}")
    else:
        print(f"❌ Failed to batch task {task_id}")


async def batch_all(tm: TaskManager, max_tasks: int = 20):
    """Batch all unbatched tasks."""
    print(f"\n⏳ Finding and batching up to {max_tasks} unbatched tasks...")
    
    batch_id = await tm.batch_multiple_tasks(max_tasks=max_tasks)
    
    if batch_id:
        print(f"✅ Tasks batched successfully: {batch_id}")
    else:
        print("❌ Failed to batch tasks (or no tasks to batch)")


async def health_summary(tm: TaskManager):
    """Show health summary."""
    health = tm.get_health_summary()
    
    print(f"\n{'='*60}")
    print("📊 TASK BOARD HEALTH SUMMARY")
    print('='*60)
    
    summary = health['summary']
    print(f"\nTotal Tasks: {summary['total_tasks']}")
    print(f"Health Score: {summary['health_score']}")
    print(f"\nStale Tasks: {summary['stale_count']}")
    print(f"Unassigned High Priority: {summary['unassigned_high_priority_count']}")
    print(f"Missing Artifacts: {summary['missing_artifacts_count']}")
    
    if 'batch_stats' in health:
        batch_stats = health['batch_stats']
        print(f"\nBatch Processing:")
        print(f"  Total Batched: {batch_stats['total_batched']}")
        if batch_stats['batched_tasks']:
            print(f"  Batched Tasks: {', '.join(batch_stats['batched_tasks'][:5])}")
            if len(batch_stats['batched_tasks']) > 5:
                print(f"    ... and {len(batch_stats['batched_tasks']) - 5} more")
    
    print('='*60)


async def workspace_scan(ws):
    """Scan workspace for large files."""
    print("\n🔍 Scanning workspace for large files (>10MB)...")
    large_files = ws.find_large_files(min_size_mb=10)
    
    if not large_files:
        print("✅ No large files found.")
        return
        
    print(f"\n📦 Found {len(large_files)} large files:")
    for path, size in large_files:
        print(f"  • {path} ({size:.2f} MB)")


async def workspace_duplicates(ws):
    """Scan for duplicate files."""
    print("\n👯 Scanning for duplicate files...")
    duplicates = ws.find_duplicates()
    
    if not duplicates:
        print("✅ No duplicate files found.")
        return
        
    print(f"\n📂 Found {len(duplicates)} sets of duplicates:")
    for file_hash, paths in duplicates.items():
        print(f"  • Hash {file_hash[:8]}...: {len(paths)} copies")
        for path in paths:
            print(f"    - {path}")


async def workspace_cleanup(ws, dry_run: bool = True):
    """Cleanup workspace duplicates and temp files."""
    action = "DRY RUN: Would cleanup" if dry_run else "Cleaning up"
    print(f"\n🧹 {action} workspace...")
    
    deleted_dups = ws.cleanup_duplicates(dry_run=dry_run)
    deleted_temps = ws.cleanup_temp_files(dry_run=dry_run)
    
    dup_count = len(deleted_dups)
    temp_count = len(deleted_temps)
    
    if dry_run:
        print(f"  • Would delete {dup_count} duplicate files")
        print(f"  • Would delete {temp_count} temp files")
    else:
        print(f"  ✅ Deleted {dup_count} duplicate files")
        print(f"  ✅ Deleted {temp_count} temp files")


async def workspace_report(ws):
    """Generate and save workspace health report."""
    print("\n📋 Generating workspace health report...")
    report = ws.generate_workspace_report()
    ws.save_report(report)
    
    print(f"\nHealth Score: {report['health_score']}")
    print(f"Duplicates: {report['duplicates']['redundant_files']} files ({report['duplicates']['wasted_space_mb']} MB wasted)")
    print(f"Temp Files: {report['temp_files']['count']} files")
    
    if report['runaway_bot_check']['is_runaway']:
        print("\n⚠️  WARNING: Runaway bot activity detected!")
    else:
        print("\n✅ No runaway bot activity detected.")
        
    print("\n✅ Report saved to artifacts/workspace_health.json")


async def detect_runaway(ws):
    """Check for runaway bot activity."""
    print("\n🤖 Checking for runaway bot activity...")
    result = ws.detect_runaway_bot()
    
    if result['is_runaway']:
        print("\n🚨 ALERT: Runaway bot detected!")
        print(f"  • Files per minute: {result['files_per_minute']}")
        print(f"  • Recent duplicates: {result['recent_duplicates']}")
    else:
        print("\n✅ System behavior appears normal.")
        print(f"  • Recent files: {result['recent_files_count']}")
        print(f"  • Creation rate: {result['files_per_minute']}/min")


async def workspace_defrag(ws, dry_run: bool = True):
    """Consolidate workspace structure."""
    action = "DRY RUN: Would defrag" if dry_run else "Defragmenting"
    print(f"\n🏗️  {action} workspace...")
    
    results = ws.defrag_workspace(dry_run=dry_run)
    
    if not results:
        print("✅ Workspace already optimized.")
        return
        
    for res in results:
        print(f"  • {res}")


async def run_heartbeat(tm: TaskManager, client_id: str | None = None):
    """Register client and start heartbeat loop."""
    if not client_id:
        client_id = f"client-{socket.gethostname()}-{platform.system().lower()}"
    
    hostname = socket.gethostname()
    print(f"\n💓 Starting heartbeat for {client_id}...")
    
    tm.register_client(client_id, hostname)
    
    try:
        import psutil
    except ImportError:
        psutil = None
        print("⚠️  psutil not found, metrics will be limited.")

    while True:
        cpu = int(psutil.cpu_percent()) if psutil else 0
        mem = int(psutil.virtual_memory().percent) if psutil else 0
        
        tm.update_heartbeat(client_id, cpu, mem)
        tm.check_client_timeouts() # Hub-like behavior for local testing
        
        print(f"  [Heartbeat] {datetime.now().strftime('%H:%M:%S')} - CPU: {cpu}% MEM: {mem}%", end="\r")
        await asyncio.sleep(30)


async def generate_docs():
    """Generate API documentation for core managers."""
    print("\n📚 Generating API documentation...")
    from scripts.docs_generator import DocsGenerator
    generator = DocsGenerator()
    generator.run()
    print("\n✅ Documentation generated in docs/api/")


async def run_devtoys(task_name: str, text: str = "", pattern: str = ""):
    """Run a DevToys utility."""
    print(f"\n🛠️  Running DevToys task: {task_name}...")
    from plugins.devtoys.devtoys_plugin import DevToysPlugin
    from plugins.devtoys.config import DevToysConfig
    
    config = DevToysConfig(sdk_path=Path(".")) # Dummy path for now
    plugin = DevToysPlugin(config)
    
    result = await plugin.run_task(task_name, text=text, pattern=pattern)
    print(f"\nResult:\n{result}")


async def run_ngrok(action: str, port: int = 8000):
    """Manage ngrok tunnel."""
    from core.services import NgrokPlugin, NgrokConfig
    from pydantic import SecretStr
    import os
    
    auth_token = os.getenv("NGROK_AUTH_TOKEN", "dummy_token")
    config = NgrokConfig(auth_token=SecretStr(auth_token), port=port)
    plugin = NgrokPlugin(config)
    
    if action == "start":
        print(f"\n🚀 Starting ngrok tunnel on port {port}...")
        url = await plugin.start()
        if url:
            print(f"✅ Tunnel started: {url}")
        else:
            print("❌ Failed to start tunnel")
    elif action == "stop":
        print("\n🛑 Stopping ngrok tunnel...")
        await plugin.stop()
        print("✅ Tunnel stopped")
    elif action == "status":
        status = plugin.status
        print(f"\n📊 ngrok Status:")
        print(f"  Running: {status['is_running']}")
        print(f"  URL: {status['public_url']}")


async def subscribe_tasks(client_id: str | None = None):
    """Subscribe to real-time task updates via gRPC."""
    import grpc
    from core.ipc.protos import bridge_pb2, bridge_pb2_grpc
    
    if not client_id:
        client_id = f"subscriber-{socket.gethostname()}"
        
    print(f"\n📡 Subscribing to task updates as {client_id}...")
    
    async with grpc.aio.insecure_channel('localhost:50051') as channel:
        stub = bridge_pb2_grpc.BridgeStub(channel)
        request = bridge_pb2.SubscribeRequest(client_id=client_id)
        
        try:
            async for update in stub.SubscribeToTasks(request):
                print(f"\n🔔 [TASK {update.event_type}] {update.task_id}: {update.title}")
                print(f"   Status: {update.status} | Assignee: {update.assignee}")
                print(f"   Time: {datetime.fromtimestamp(update.timestamp).strftime('%H:%M:%S')}")
        except grpc.aio.AioRpcError as e:
            print(f"\n❌ gRPC Error: {e.details()}")
        except KeyboardInterrupt:
            print("\n👋 Unsubscribing...")


async def main():
    """Main CLI entry point."""
    if len(sys.argv) < 2:
        print(__doc__)
        sys.exit(1)
    
    command = sys.argv[1]
    
    # Initialize Hub
    logger.info("Initializing ManagerHub...")
    try:
        from core.managers import ManagerHub
        hub = ManagerHub.create()
    except Exception:
        # Fallback for development if .env is missing
        import os
        if not os.getenv("OPENAI_API_KEY"):
            os.environ["OPENAI_API_KEY"] = "sk-dummy-key-for-cli-operations"
        from core.managers import ManagerHub
        hub = ManagerHub.create()
        
    tm = hub.tasks
    
    try:
        if command == "list-unbatched":
            max_count = int(sys.argv[2]) if len(sys.argv) > 2 else 10
            await list_unbatched(tm, max_count)
        
        elif command == "find-next":
            await find_next(tm)
        
        elif command == "claim":
            task_id = sys.argv[2] if len(sys.argv) > 2 else None
            await claim_task(tm, task_id)
        
        elif command == "status":
            if len(sys.argv) < 3:
                print("❌ Error: task_id required")
                sys.exit(1)
            await task_status(tm, sys.argv[2])
        
        elif command == "batch":
            if len(sys.argv) < 3:
                print("❌ Error: task_id required")
                sys.exit(1)
            await batch_task(tm, sys.argv[2])
        
        elif command == "batch-all":
            max_tasks = 20
            if len(sys.argv) > 2 and sys.argv[2] == "--max":
                max_tasks = int(sys.argv[3])
            await batch_all(tm, max_tasks)
        
        elif command == "health":
            await health_summary(tm)
        
        elif command == "workspace-scan":
            await workspace_scan(hub.workspace)
        
        elif command == "workspace-duplicates":
            await workspace_duplicates(hub.workspace)
        
        elif command == "workspace-cleanup":
            dry_run = "--dry-run" in sys.argv or "-d" in sys.argv
            await workspace_cleanup(hub.workspace, dry_run)
        
        elif command == "workspace-report":
            await workspace_report(hub.workspace)
        
        elif command == "detect-runaway":
            await detect_runaway(hub.workspace)
        
        elif command == "workspace-defrag":
            dry_run = "--dry-run" in sys.argv or "-d" in sys.argv
            await workspace_defrag(hub.workspace, dry_run)
            
        elif command == "heartbeat":
            client_id = None
            if "--client-id" in sys.argv:
                idx = sys.argv.index("--client-id")
                if len(sys.argv) > idx + 1:
                    client_id = sys.argv[idx + 1]
            await run_heartbeat(tm, client_id)
            
        elif command == "subscribe":
            client_id = None
            if "--client-id" in sys.argv:
                idx = sys.argv.index("--client-id")
                if len(sys.argv) > idx + 1:
                    client_id = sys.argv[idx + 1]
            await subscribe_tasks(client_id)
            
        elif command == "docs-generate":
            await generate_docs()
            
        elif command == "devtoys":
            if len(sys.argv) < 3:
                print("❌ Error: task_name required")
                sys.exit(1)
            
            task_name = sys.argv[2]
            text = ""
            pattern = ""
            
            if "--text" in sys.argv:
                text = sys.argv[sys.argv.index("--text") + 1]
            if "--pattern" in sys.argv:
                pattern = sys.argv[sys.argv.index("--pattern") + 1]
                
            await run_devtoys(task_name, text, pattern)

        elif command == "ngrok":
            if len(sys.argv) < 3:
                print("❌ Error: action [start|stop|status] required")
                sys.exit(1)
            
            action = sys.argv[2]
            port = 8000
            if "--port" in sys.argv:
                port = int(sys.argv[sys.argv.index("--port") + 1])
                
            await run_ngrok(action, port)

        elif command == "add":
            priority = "medium"
            title = ""
            description = ""
            task_type = "feature"
            depends_on = "-"
            
            if "--priority" in sys.argv:
                priority = sys.argv[sys.argv.index("--priority") + 1]
            if "--title" in sys.argv:
                title = sys.argv[sys.argv.index("--title") + 1]
            if "--description" in sys.argv:
                description = sys.argv[sys.argv.index("--description") + 1]
            if "--type" in sys.argv:
                task_type = sys.argv[sys.argv.index("--type") + 1]
            if "--depends" in sys.argv:
                depends_on = sys.argv[sys.argv.index("--depends") + 1]
                
            if not title:
                print("❌ Error: --title required")
                sys.exit(1)
                
            await add_task(tm, priority, title, description, task_type, depends_on)
            
        elif command == "complete":
            if len(sys.argv) < 3:
                print("❌ Error: task_id required")
                sys.exit(1)
            await complete_task(tm, sys.argv[2])

        elif command == "decompose":
            goal = ""
            priority = "medium"
            task_type = "feature"

            if "--goal" in sys.argv:
                goal = sys.argv[sys.argv.index("--goal") + 1]
            if "--priority" in sys.argv:
                priority = sys.argv[sys.argv.index("--priority") + 1]
            if "--type" in sys.argv:
                task_type = sys.argv[sys.argv.index("--type") + 1]

            if not goal:
                print("❌ Error: --goal required")
                sys.exit(1)

            await decompose_goal(tm, goal, priority, task_type)
            
        else:
            print(f"❌ Unknown command: {command}")
            print(__doc__)
            sys.exit(1)
    
    except KeyboardInterrupt:
        print("\n\n⚠️  Interrupted by user")
    except Exception as e:
        logger.error(f"Command failed: {e}")
        print(f"\n❌ Error: {e}")
        sys.exit(1)


if __name__ == "__main__":
    asyncio.run(main())

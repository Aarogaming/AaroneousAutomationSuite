import asyncio
import sys
from loguru import logger
from core.config.manager import load_config
from core.ipc.server import serve_ipc
from core.handoff.manager import HandoffManager

async def main():
    logger.info("Initializing Aaroneous Automation Suite (AAS) Hub...")
    
    # 1. Load Resilient Configuration
    try:
        config = load_config()
    except Exception:
        logger.critical("Failed to load configuration. Hub cannot start.")
        return

    # 2. Initialize Handoff Manager
    handoff = HandoffManager()
    
    # Handle CLI commands for task claiming
    if len(sys.argv) > 1:
        cmd = sys.argv[1].lower()
        if cmd == "claim":
            actor = sys.argv[2] if len(sys.argv) > 2 else "Sixth"
            task = handoff.claim_next_task(actor)
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
                print("\nUsage: python core/main.py complete [TaskID]\n")
                return
            task_id = sys.argv[2]
            if handoff.complete_task(task_id):
                print(f"\nTask {task_id} marked as Done.\n")
            else:
                print(f"\nTask {task_id} not found or already completed.\n")
            return
        elif cmd == "board":
            _, tasks, status_map = handoff.parse_board()
            blocked_tasks = handoff.get_blocked_tasks()
            
            print("\n--- AAS ACTIVE TASK BOARD ---")
            print(f"{'ID':<10} | {'Priority':<10} | {'Status':<12} | {'Title'}")
            print("-" * 80)
            for t in tasks:
                # Check if blocked
                blocked = False
                dep_str = ""
                if t["depends_on"] and t["depends_on"] != "-":
                    dep_ids = [d.strip() for d in t["depends_on"].split(",")]
                    blocked = any(status_map.get(dep_id) != "Done" for dep_id in dep_ids)
                    dep_str = f" (Blocked by: {t['depends_on']})" if blocked else ""
                
                status = f"BLOCKED" if blocked and t["status"] == "queued" else t["status"]
                print(f"{t['id']:<10} | {t['priority']:<10} | {status:<12} | {t['title']}{dep_str}")
            print("-" * 80)
            
            # Show summary statistics
            total = len(tasks)
            done = sum(1 for t in tasks if t["status"] == "Done")
            in_progress = sum(1 for t in tasks if t["status"] == "In Progress")
            queued = sum(1 for t in tasks if t["status"] == "queued")
            blocked_count = len(blocked_tasks)
            
            print(f"\n📊 Summary: {done} Done | {in_progress} In Progress | {queued} Queued | {blocked_count} Blocked")
            
            if blocked_tasks:
                print(f"\n🔒 Blocked Tasks ({blocked_count}):")
                for bt in blocked_tasks[:5]:  # Show first 5
                    print(f"   - {bt['id']} waiting on {', '.join(bt['blocking_tasks'])}")
                if len(blocked_tasks) > 5:
                    print(f"   ... and {len(blocked_tasks) - 5} more")
            
            print()
            return
        elif cmd == "blocked":
            blocked_tasks = handoff.get_blocked_tasks()
            
            if not blocked_tasks:
                print("\n✅ No blocked tasks! All dependencies are satisfied.\n")
                return
            
            print(f"\n🔒 BLOCKED TASKS ({len(blocked_tasks)})")
            print("-" * 80)
            
            for bt in blocked_tasks:
                blocking = ", ".join(bt['blocking_tasks'])
                print(f"\n{bt['id']} [{bt['priority'].upper()}]: {bt['title']}")
                print(f"   Waiting on: {blocking}")
            
            print("\n" + "-" * 80)
            print(f"Total: {len(blocked_tasks)} tasks blocked\n")
            return
    ipc_task = asyncio.create_task(serve_ipc(port=config.ipc_port))

    logger.success("AAS Hub is now running and awaiting Maelstrom connection.")
    
    try:
        await asyncio.gather(ipc_task)
    except asyncio.CancelledError:
        logger.info("AAS Hub shutting down...")

if __name__ == "__main__":
    asyncio.run(main())

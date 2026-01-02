import asyncio
import sys
import argparse
from loguru import logger
from core.config.manager import load_config
from core.ipc.server import serve_ipc
from core.handoff.manager import HandoffManager

class TaskCLI:
    """CLI interface for task management operations"""
    
    def __init__(self, handoff: HandoffManager):
        self.handoff = handoff
    
    def create_task(self, title: str, priority: str = "Medium", depends: str = None, description: str = None):
        """Create a new task"""
        _, tasks, _ = self.handoff.parse_board()
        
        # Generate next task ID
        max_id = max([int(t['id'].split('-')[1]) for t in tasks if t['id'].startswith('AAS-')], default=106)
        new_id = f"AAS-{max_id + 1}"
        
        # Format dependencies
        deps_str = depends if depends else "-"
        desc_str = description if description else title
        
        # Read current board
        with open("handoff/ACTIVE_TASKS.md", "r") as f:
            content = f.read()
        
        # Add to task table
        import datetime
        today = datetime.datetime.now().strftime("%Y-%m-%d")
        new_row = f" | {new_id} | {priority} | {title} | {deps_str} | queued | - | {today} | {today} | \n"
        
        # Insert before "## Task Details"
        content = content.replace("\n## Task Details", f"{new_row}\n## Task Details")
        
        # Add task detail section
        detail = f"\n### {new_id}: {title}\n- **Description**: {desc_str}\n"
        if depends:
            detail += f"- **Dependencies**: {depends}\n"
        detail += f"- **Priority**: {priority}\n- **Type**: enhancement\n"
        
        content += detail
        
        # Write back
        with open("handoff/ACTIVE_TASKS.md", "w") as f:
            f.write(content)
        
        print(f"\n[OK] Created task {new_id}: {title}")
        print(f"     Priority: {priority} | Dependencies: {deps_str}\n")
        return new_id
    
    def start_task(self, task_id: str, actor: str = "Copilot"):
        """Start (claim) a task"""
        _, tasks, status_map = self.handoff.parse_board()
        
        # Find task
        task = next((t for t in tasks if t['id'] == task_id), None)
        if not task:
            print(f"\n[ERROR] Task {task_id} not found\n")
            return False
        
        # Check if already started
        if task['status'] != 'queued':
            print(f"\n[ERROR] Task {task_id} is already {task['status']}\n")
            return False
        
        # Check dependencies
        if task['depends_on'] and task['depends_on'] != '-':
            dep_ids = [d.strip() for d in task['depends_on'].split(',')]
            unmet = [d for d in dep_ids if status_map.get(d.split()[0]) != 'Done' and '[OK]' not in d]
            if unmet:
                print(f"\n[ERROR] Cannot start {task_id} - blocked by: {', '.join(unmet)}\n")
                return False
        
        # Update status
        with open("handoff/ACTIVE_TASKS.md", "r") as f:
            content = f.read()
        
        import datetime, re
        today = datetime.datetime.now().strftime("%Y-%m-%d")
        
        # Update table row
        old_row = f" | {task_id} | {task['priority']} | {task['title']} | {task['depends_on']} | queued | - |"
        new_row = f" | {task_id} | {task['priority']} | {task['title']} | {task['depends_on']} | In Progress | {actor} |"
        content = content.replace(old_row, new_row)
        
        # Update the date in the row
        content = re.sub(
            rf"\| {task_id} \| {task['priority']} \| {task['title']} \| {task['depends_on']} \| In Progress \| {actor} \| [^|]+ \| [^|]+ \|",
            f"| {task_id} | {task['priority']} | {task['title']} | {task['depends_on']} | In Progress | {actor} | {task.get('created', today)} | {today} |",
            content
        )
        
        with open("handoff/ACTIVE_TASKS.md", "w") as f:
            f.write(content)
        
        print(f"\n[OK] Task {task_id} claimed by {actor}")
        print(f"     Title: {task['title']}")
        print(f"     Artifacts: artifacts/handoff/{task_id}/\n")
        return True
    
    def complete_task(self, task_id: str):
        """Mark task as complete"""
        return self.handoff.complete_task(task_id)
    
    def list_tasks(self, status: str = None, priority: str = None, assignee: str = None):
        """List tasks with optional filters"""
        _, tasks, _ = self.handoff.parse_board()
        
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
        _, tasks, status_map = self.handoff.parse_board()
        
        task = next((t for t in tasks if t['id'] == task_id), None)
        if not task:
            print(f"\n[ERROR] Task {task_id} not found\n")
            return
        
        print(f"\nTASK DETAILS: {task_id}")
        print("=" * 80)
        print(f"Title:        {task['title']}")
        print(f"Priority:     {task['priority']}")
        print(f"Status:       {task['status']}")
        print(f"Assignee:     {task.get('assignee', 'Unassigned')}")
        print(f"Dependencies: {task.get('depends_on', 'None')}")
        
        # Check if blocked
        if task['depends_on'] and task['depends_on'] != '-':
            dep_ids = [d.strip() for d in task['depends_on'].split(',')]
            unmet = [d for d in dep_ids if status_map.get(d.split()[0]) != 'Done' and '[OK]' not in d]
            if unmet:
                print(f"[!] BLOCKED BY:  {', '.join(unmet)}")
        
        print(f"Created:      {task.get('created', 'Unknown')}")
        print(f"Updated:      {task.get('updated', 'Unknown')}")
        print("=" * 80 + "\n")
    
    def available_tasks(self):
        """Show tasks that can be claimed (queued with met dependencies)"""
        _, tasks, status_map = self.handoff.parse_board()
        
        available = []
        for t in tasks:
            if t['status'] != 'queued':
                continue
            
            # Check dependencies
            if not t['depends_on'] or t['depends_on'] == '-':
                available.append(t)
            else:
                dep_ids = [d.strip() for d in t['depends_on'].split(',')]
                if all(status_map.get(d.split()[0]) == 'Done' or '[OK]' in d for d in dep_ids):
                    available.append(t)
        
        if not available:
            print("\n[!] No tasks available to claim right now\n")
            return
        
        # Sort by priority
        priority_order = {'Urgent': 0, 'High': 1, 'Medium': 2, 'Low': 3}
        available.sort(key=lambda x: priority_order.get(x['priority'], 4))
        
        print(f"\nAVAILABLE TASKS ({len(available)})")
        print("-" * 100)
        print(f"{'ID':<12} | {'Priority':<10} | {'Title'}")
        print("-" * 100)
        
        for t in available:
            print(f"{t['id']:<12} | {t['priority']:<10} | {t['title']}")
        
        print("-" * 100)
        print(f"\nUse: python -m core.main task start <ID> [actor_name]\n")

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
    task_cli = TaskCLI(handoff)
    
    # Handle CLI commands
    if len(sys.argv) > 1:
        cmd = sys.argv[1].lower()
        
        # Task management subcommands
        if cmd == "task":
            if len(sys.argv) < 3:
                print("\nUsage: python -m core.main task <command> [args]")
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
                    print("\nUsage: python -m core.main task create <title> [--priority High] [--depends AAS-001]\n")
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
                    print("\nUsage: python -m core.main task start <task_id> [actor_name]\n")
                    return
                task_id = sys.argv[3]
                actor = sys.argv[4] if len(sys.argv) > 4 else "Copilot"
                task_cli.start_task(task_id, actor)
            
            elif subcmd == "complete":
                if len(sys.argv) < 4:
                    print("\nUsage: python -m core.main task complete <task_id>\n")
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
                    print("\nUsage: python -m core.main task show <task_id>\n")
                    return
                task_id = sys.argv[3]
                task_cli.show_task(task_id)
            
            elif subcmd == "available":
                task_cli.available_tasks()
            
            else:
                print(f"\n[ERROR] Unknown task command: {subcmd}\n")
            
            return
        
        # Legacy commands (maintained for backward compatibility)
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
            
            print(f"\n Summary: {done} Done | {in_progress} In Progress | {queued} Queued | {blocked_count} Blocked")
            
            if blocked_tasks:
                print(f"\n Blocked Tasks ({blocked_count}):")
                for bt in blocked_tasks[:5]:  # Show first 5
                    print(f"   - {bt['id']} waiting on {', '.join(bt['blocking_tasks'])}")
                if len(blocked_tasks) > 5:
                    print(f"   ... and {len(blocked_tasks) - 5} more")
            
            print()
            return
        elif cmd == "blocked":
            blocked_tasks = handoff.get_blocked_tasks()
            
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
    ipc_task = asyncio.create_task(serve_ipc(port=config.ipc_port))

    logger.success("AAS Hub is now running and awaiting Maelstrom connection.")
    
    try:
        await asyncio.gather(ipc_task)
    except asyncio.CancelledError:
        logger.info("AAS Hub shutting down...")

if __name__ == "__main__":
    asyncio.run(main())

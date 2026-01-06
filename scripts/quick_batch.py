"""Quick script to check queued tasks and submit batches."""
import sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).parent.parent))

from core.config import load_config
from core.handoff_manager import HandoffManager
import asyncio

async def main():
    config = load_config()
    hm = HandoffManager(config)
    
    # Parse board and get queued tasks
    lines, all_tasks, status_map = hm.parse_board()
    tasks = [t for t in all_tasks if t['status'].lower() == 'queued']
    
    print(f"\n✅ Found {len(tasks)} queued tasks:\n")
    
    for t in tasks:
        print(f"  {t['id']:8} | {t.get('priority', 'medium'):6} | {t['title']}")
    
    if not tasks:
        print("No queued tasks to batch. Checking other statuses...")
        todo_tasks = [t for t in all_tasks if t['status'].lower() in ['todo', 'backlog']]
        print(f"\nTODO/Backlog tasks: {len(todo_tasks)}")
        for t in todo_tasks[:5]:
            print(f"  {t['id']:8} | {t.get('priority', 'medium'):6} | {t['title']}")
        return
    
    # Submit batch
    print(f"\n🚀 Submitting batch for {len(tasks)} queued tasks...\n")
    
    if hm.batch_processor:
        result = await hm.batch_analyze_queued_tasks()
        print(f"\n✅ Batch submitted successfully!")
        print(f"   Batch ID: {result.get('batch_id')}")
        print(f"   Tasks: {result.get('task_count')}")
        print(f"   Status: {result.get('status')}")
    else:
        print("❌ Batch processor not initialized (check OPENAI_API_KEY)")

if __name__ == "__main__":
    asyncio.run(main())

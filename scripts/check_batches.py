"""Quick script to check batch status"""
import asyncio
from core.managers.batch import BatchManager
from core.config.manager import load_config

async def main():
    bm = BatchManager(load_config())
    
    batch_ids = [
        'batch_6959bf81f4588190ba2f533dffd5005e',  # 6 tasks
        'batch_6959c7f462008190ac8888fda6d28d7c',  # 3 tasks
    ]
    
    for batch_id in batch_ids:
        try:
            batch = bm.get_batch_status(batch_id)  # Not async!
            print(f"\n{'='*60}")
            print(f"📦 Batch: {batch_id}")
            print(f"   Status: {batch['status']}")
            print(f"   Created: {batch['created_at']}")
            print(f"   Requests: {batch['request_counts']['total']} total, "
                  f"{batch['request_counts']['completed']} completed, "
                  f"{batch['request_counts']['failed']} failed")
        except Exception as e:
            print(f"\n❌ Error checking {batch_id}: {e}")

if __name__ == "__main__":
    asyncio.run(main())

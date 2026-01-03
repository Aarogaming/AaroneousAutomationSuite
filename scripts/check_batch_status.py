"""Quick script to check batch status"""
import sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).parent.parent))

from openai import OpenAI
from core.config.manager import AASConfig

config = AASConfig()
client = OpenAI(api_key=config.openai_api_key.get_secret_value())

# Check the active batch
batch_id = "batch_69584040cec481909fc0163f3b46f79e"
print(f"Checking batch: {batch_id}\n")

try:
    batch = client.batches.retrieve(batch_id)
    print(f"Status: {batch.status}")
    print(f"Created: {batch.created_at}")
    print(f"Request counts: {batch.request_counts}")
    
    if batch.status == "completed":
        print("\n✅ Batch is COMPLETED! Ready to retrieve results.")
    elif batch.status == "failed":
        print("\n❌ Batch FAILED")
        if hasattr(batch, 'errors'):
            print(f"Errors: {batch.errors}")
    elif batch.status in ["validating", "in_progress", "finalizing"]:
        print(f"\n⏳ Batch is {batch.status.upper()}... still processing")
    else:
        print(f"\n📊 Batch status: {batch.status}")
        
except Exception as e:
    print(f"❌ Error checking batch: {e}")

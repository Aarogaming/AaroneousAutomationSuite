"""Retrieve completed batch results"""
import sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).parent.parent))

import json
from openai import OpenAI
from core.config import AASConfig
from datetime import datetime

config = AASConfig()
client = OpenAI(api_key=config.openai_api_key.get_secret_value())

# Batch info
batch_id = "batch_69584040cec481909fc0163f3b46f79e"
task_id = "AAS-113"  # From monitor_state.json

print(f"🔍 Retrieving batch: {batch_id}")
print(f"   Task: {task_id}\n")

try:
    # Get batch details
    batch = client.batches.retrieve(batch_id)
    print(f"Status: {batch.status}")
    print(f"Request counts: {batch.request_counts}")
    
    if batch.status == "completed":
        print("\n✅ Batch completed! Downloading results...\n")
        
        # Get output file
        output_file_id = batch.output_file_id
        print(f"Output file ID: {output_file_id}")
        
        # Download results
        result_content = client.files.content(output_file_id)
        result_text = result_content.text
        
        # Parse results
        results = []
        for line in result_text.strip().split('\n'):
            if line:
                results.append(json.loads(line))
        
        print(f"\n📊 Results ({len(results)} response(s)):\n")
        
        # Save to file
        output_path = Path("artifacts/batch/results") / f"{batch_id}_processed.json"
        output_path.parent.mkdir(parents=True, exist_ok=True)
        
        with open(output_path, 'w') as f:
            json.dump({
                "batch_id": batch_id,
                "task_id": task_id,
                "retrieved_at": datetime.utcnow().isoformat(),
                "request_counts": {
                    "completed": batch.request_counts.completed,
                    "failed": batch.request_counts.failed,
                    "total": batch.request_counts.total
                },
                "results": results
            }, f, indent=2)
        
        print(f"💾 Saved to: {output_path}")
        
        # Display summary
        print("\n" + "="*70)
        for i, result in enumerate(results, 1):
            if result.get('response'):
                response = result['response']
                if response.get('body'):
                    body = response['body']
                    if 'choices' in body:
                        content = body['choices'][0]['message']['content']
                        print(f"\nResult {i}:")
                        print(f"  Custom ID: {result.get('custom_id', 'N/A')}")
                        print(f"  Content preview: {content[:200]}...")
                        print(f"  Full length: {len(content)} characters")
            elif result.get('error'):
                print(f"\n❌ Error in result {i}: {result['error']}")
        
        print("\n" + "="*70)
        print(f"\n✅ Batch {batch_id} processed successfully!")
        print(f"   Task: {task_id}")
        print(f"   Results file: {output_path}")
        
    else:
        print(f"\n⏳ Batch not ready yet (status: {batch.status})")
        
except Exception as e:
    print(f"\n❌ Error retrieving batch: {e}")
    import traceback
    traceback.print_exc()

"""Retrieve and save results from both completed batches"""
import sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).parent.parent))

import json
from openai import OpenAI
from core.config.manager import load_config
from datetime import datetime
from loguru import logger

config = load_config()
client = OpenAI(api_key=config.openai_api_key.get_secret_value())

# Both completed batches
batches = [
    'batch_6959bf81f4588190ba2f533dffd5005e',  # 6 tasks
    'batch_6959c7f462008190ac8888fda6d28d7c',  # 3 tasks
]

def retrieve_batch(batch_id: str):
    """Retrieve and save results for a single batch"""
    try:
        logger.info(f"🔍 Retrieving batch: {batch_id}")
        
        # Get batch details
        batch = client.batches.retrieve(batch_id)
        
        if batch.status != "completed":
            logger.warning(f"Batch {batch_id} not completed yet: {batch.status}")
            return None
        
        logger.success(f"✅ Batch completed! Downloading results...")
        
        # Get output file
        output_file_id = batch.output_file_id
        result_content = client.files.content(output_file_id)
        result_text = result_content.text
        
        # Parse results
        results = []
        for line in result_text.strip().split('\n'):
            if line:
                results.append(json.loads(line))
        
        logger.info(f"📊 Retrieved {len(results)} result(s)")
        
        # Save to file
        output_path = Path("artifacts/batch/results") / f"{batch_id}_results.json"
        output_path.parent.mkdir(parents=True, exist_ok=True)
        
        with open(output_path, 'w', encoding='utf-8') as f:
            json.dump({
                "batch_id": batch_id,
                "retrieved_at": datetime.utcnow().isoformat(),
                "request_counts": {
                    "completed": batch.request_counts.completed,
                    "failed": batch.request_counts.failed,
                    "total": batch.request_counts.total
                },
                "metadata": batch.metadata,
                "results": results
            }, f, indent=2)
        
        logger.success(f"💾 Saved to: {output_path}")
        
        # Display summary
        print(f"\n{'='*70}")
        print(f"Batch: {batch_id}")
        print(f"Results: {len(results)}")
        print(f"{'='*70}")
        
        for i, result in enumerate(results, 1):
            custom_id = result.get('custom_id', 'N/A')
            
            if result.get('response'):
                response = result['response']
                if response.get('body'):
                    body = response['body']
                    if 'choices' in body:
                        content = body['choices'][0]['message']['content']
                        print(f"\n{i}. Task: {custom_id}")
                        print(f"   Length: {len(content)} characters")
                        print(f"   Preview: {content[:150]}...")
            elif result.get('error'):
                print(f"\n{i}. ❌ Task {custom_id} - Error: {result['error']}")
        
        return output_path
        
    except Exception as e:
        logger.error(f"Failed to retrieve batch {batch_id}: {e}")
        return None

if __name__ == "__main__":
    print("🚀 Retrieving results from completed batches...\n")
    
    saved_files = []
    for batch_id in batches:
        output_file = retrieve_batch(batch_id)
        if output_file:
            saved_files.append(output_file)
        print()  # Blank line between batches
    
    print(f"\n{'='*70}")
    print(f"✅ Retrieved {len(saved_files)} batch(es)")
    for file in saved_files:
        print(f"   📄 {file}")
    print(f"{'='*70}")

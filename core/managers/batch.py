"""
Batch Manager - Unified OpenAI Batch API operations.

Consolidates logic from BatchManager and BatchProcessor into a single,
standardized manager.
"""

import json
import uuid
from pathlib import Path
from typing import Optional, Dict, Any, List
from loguru import logger
import openai
from core.managers.protocol import ManagerProtocol


class BatchManager(ManagerProtocol):
    """Unified manager for OpenAI Batch API operations."""
    
    def __init__(self, config):
        self.config = config
        self.client = openai.OpenAI(api_key=config.openai_api_key.get_secret_value())
        self.batch_dir = Path("artifacts/batch")
        self.batch_dir.mkdir(parents=True, exist_ok=True)
        logger.info("BatchManager initialized")

    async def submit_batch(
        self,
        requests: List[Dict[str, Any]],
        description: str,
        metadata: Optional[Dict[str, Any]] = None
    ) -> str:
        """Submit a batch job with automatic request formatting."""
        try:
            # 1. Create JSONL locally
            batch_uuid = uuid.uuid4().hex[:32]
            input_file = self.batch_dir / f"batch_{batch_uuid}_input.jsonl"
            with open(input_file, 'w', encoding='utf-8') as f:
                for req in requests:
                    f.write(json.dumps(req) + '\n')
            
            # 2. Upload to OpenAI
            with open(input_file, 'rb') as f:
                file_obj = self.client.files.create(file=f, purpose='batch')
            
            # 3. Submit batch
            batch = self.client.batches.create(
                input_file_id=file_obj.id,
                endpoint="/v1/chat/completions",
                completion_window="24h",
                metadata=metadata or {}
            )
            
            logger.success(f"Submitted batch {batch.id}: {description}")
            return batch.id
            
        except Exception as e:
            logger.error(f"Failed to submit batch: {e}")
            raise

    def get_batch_status(self, batch_id: str) -> Dict[str, Any]:
        """Get batch status and progress."""
        try:
            batch = self.client.batches.retrieve(batch_id)
            return {
                'id': batch.id,
                'status': batch.status,
                'created_at': batch.created_at,
                'request_counts': {
                    'total': batch.request_counts.total,
                    'completed': batch.request_counts.completed,
                    'failed': batch.request_counts.failed
                },
                'metadata': batch.metadata
            }
        except Exception as e:
            logger.error(f"Failed to get batch status for {batch_id}: {e}")
            raise

    def list_active_batches(self) -> List[Dict[str, Any]]:
        """List all active/pending batches."""
        try:
            batches = self.client.batches.list(limit=100)
            return [
                {'id': b.id, 'status': b.status, 'metadata': b.metadata}
                for b in batches.data
                if b.status in ['validating', 'in_progress', 'finalizing']
            ]
        except Exception as e:
            logger.error(f"Failed to list batches: {e}")
            return []

    # ===== Protocol Implementation =====

    def get_status(self) -> dict:
        """Return BatchManager status."""
        active = self.list_active_batches()
        return {
            "type": "BatchManager",
            "version": "2.0",
            "active_batches": len(active),
            "batch_dir": str(self.batch_dir)
        }

    def validate(self) -> bool:
        """Validate BatchManager state."""
        return self.batch_dir.exists()

    async def batch_task(self, task_id: str, task_details: Dict[str, Any]) -> Optional[str]:
        """
        High-level method to batch a single task.
        """
        prompt = f"""Task: {task_details['title']}
Task ID: {task_id}
Priority: {task_details.get('priority', 'medium')}

Provide a comprehensive implementation plan for this task following AAS conventions.
"""
        request = {
            'custom_id': task_id,
            'method': 'POST',
            'url': '/v1/chat/completions',
            'body': {
                'model': self.config.openai_model,
                'messages': [
                    {'role': 'system', 'content': 'You are an expert software architect.'},
                    {'role': 'user', 'content': prompt}
                ],
                'max_tokens': 4000,
                'temperature': 0.7
            }
        }
        
        return await self.submit_batch(
            requests=[request],
            description=f"Implementation plan for {task_id}",
            metadata={'task_id': task_id}
        )

    async def batch_multiple_tasks(self, tasks: List[Dict[str, Any]]) -> Optional[str]:
        """
        High-level method to batch multiple tasks.
        """
        requests = []
        for task in tasks:
            prompt = f"Task: {task['title']}\nTask ID: {task['id']}"
            requests.append({
                'custom_id': task['id'],
                'method': 'POST',
                'url': '/v1/chat/completions',
                'body': {
                    'model': self.config.openai_model,
                    'messages': [{'role': 'user', 'content': prompt}],
                    'max_tokens': 2000
                }
            })
        
        return await self.submit_batch(
            requests=requests,
            description=f"Multi-task batch: {len(tasks)} tasks",
            metadata={'task_count': len(tasks)}
        )

"""
Auto-Batch Task Scanner - Simple version for batch monitor
"""
import re
from pathlib import Path
from typing import List, Dict, Any, Optional
from datetime import datetime
from loguru import logger
from core.batch.processor import BatchProcessor


class AutoBatcher:
    """Simplified batch scanner and submitter for monitoring"""
    
    def __init__(self, config, dry_run: bool = False, max_tasks: int = 20):
        self.config = config
        self.dry_run = dry_run
        self.max_tasks = max_tasks
        self.processor = BatchProcessor(config) if not dry_run else None
        self.board_path = Path("handoff/ACTIVE_TASKS.md")
    
    def archive_done_tasks(self) -> int:
        """Move completed tasks to archive file.
        
        Returns:
            Number of tasks archived
        """
        if not self.board_path.exists():
            logger.warning(f"Board file not found: {self.board_path}")
            return 0
        
        # Read current board
        content = self.board_path.read_text(encoding='utf-8')
        lines = content.split('\n')
        
        # Find table boundaries
        table_start = None
        table_end = None
        for i, line in enumerate(lines):
            if '| ID |' in line and 'Status' in line:
                table_start = i
            elif table_start is not None and line.strip() and not line.strip().startswith('|'):
                table_end = i
                break
        
        if table_start is None:
            logger.warning("Could not find task table in board")
            return 0
        
        if table_end is None:
            table_end = len(lines)
        
        # Separate done tasks from active tasks
        header_lines = lines[:table_start + 2]  # Include header and separator
        active_rows = []
        done_rows = []
        
        for i in range(table_start + 2, table_end):
            line = lines[i].strip()
            if not line or not line.startswith('|'):
                continue
            
            # Check if status is 'done'
            parts = [p.strip() for p in line.split('|')]
            if len(parts) >= 6:
                status = parts[5].lower()  # Status is 6th column
                if status == 'done':
                    done_rows.append(line)
                else:
                    active_rows.append(line)
        
        if not done_rows:
            logger.debug("No completed tasks to archive")
            return 0
        
        # Update active board (remove done tasks)
        footer_lines = lines[table_end:]
        new_content = '\n'.join(header_lines + active_rows + footer_lines)
        self.board_path.write_text(new_content, encoding='utf-8')
        
        # Append to archive
        archive_path = self.board_path.parent / 'COMPLETED_TASKS.md'
        current_date = datetime.now().strftime('%Y-%m-%d')
        
        if archive_path.exists():
            archive_content = archive_path.read_text(encoding='utf-8')
        else:
            archive_content = "# Completed Tasks Archive\n\n"
        
        # Add new section for today if not exists
        section_header = f"## Completed on {current_date}\n"
        if section_header not in archive_content:
            archive_content += f"\n{section_header}\n"
            archive_content += "| ID | Priority | Title | Dependencies | Status | Started | Completed |\n"
            archive_content += "|-----|----------|-------|--------------|--------|---------|-----------||\n"
        
        # Append done tasks
        archive_content += '\n'.join(done_rows) + '\n'
        archive_path.write_text(archive_content, encoding='utf-8')
        
        logger.success(f"Archived {len(done_rows)} completed tasks to {archive_path.name}")
        return len(done_rows)
    
    def scan_board(self) -> List[Dict[str, Any]]:
        """
        Scan task board for eligible tasks.
        Returns list of task dicts with id, title, priority, status, etc.
        """
        if not self.board_path.exists():
            logger.error(f"Task board not found: {self.board_path}")
            return []
        
        content = self.board_path.read_text(encoding='utf-8')
        tasks = []
        
        # Parse table rows (format: | AAS-XXX | Priority | Title | Dependencies | Status | ...)
        for line in content.split('\n'):
            if not line.strip().startswith('|') or '---' in line:
                continue
            
            parts = [p.strip() for p in line.split('|')]
            if len(parts) < 6:
                continue
            
            task_id = parts[1]
            if not task_id or not task_id.startswith('AAS-'):
                continue
            
            priority = parts[2].lower() if len(parts) > 2 else 'medium'
            title = parts[3] if len(parts) > 3 else ''
            dependencies = parts[4] if len(parts) > 4 else '-'
            status = parts[5] if len(parts) > 5 else 'queued'
            
            # Eligibility criteria
            if status.lower() not in ['queued', 'todo']:
                continue
            if priority in ['urgent', 'high']:
                continue
            if dependencies and dependencies != '-':
                # Check if dependencies are complete (would need to parse status)
                continue
            
            tasks.append({
                'id': task_id,
                'title': title,
                'priority': priority,
                'status': status,
                'dependencies': dependencies
            })
        
        logger.info(f"Found {len(tasks)} eligible tasks from {self.board_path}")
        return tasks[:self.max_tasks]
    
    async def submit_batch(self, tasks: List[Dict[str, Any]]) -> Optional[Dict[str, Any]]:
        """Submit a batch job for the given tasks"""
        if self.dry_run:
            logger.info(f"[DRY RUN] Would submit batch for {len(tasks)} tasks")
            return {
                'batch_id': 'dry_run_batch_id',
                'task_ids': [t['id'] for t in tasks],
                'status': 'dry_run'
            }
        
        if not self.processor:
            logger.error("No processor available (dry_run mode)")
            return None
        
        # Build batch requests
        requests = []
        for task in tasks:
            custom_id = task['id']
            prompt = f"""Task: {task['title']}

Provide a detailed implementation plan for this task including:
1. Technical requirements and dependencies
2. Detailed implementation steps
3. Code examples and file structure
4. Testing strategy
5. Integration considerations"""
            
            requests.append({
                'custom_id': custom_id,
                'method': 'POST',
                'url': '/v1/chat/completions',
                'body': {
                    'model': self.config.openai_model,
                    'messages': [
                        {'role': 'system', 'content': 'You are an expert software architect and developer.'},
                        {'role': 'user', 'content': prompt}
                    ],
                    'max_tokens': 4000
                }
            })
        
        try:
            batch_id = await self.processor.submit_batch(
                requests=requests,
                description=f"Auto-batch: {len(tasks)} tasks",
                metadata={'source': 'auto_batch', 'task_count': str(len(tasks))}
            )
            logger.success(f"Submitted batch {batch_id} with {len(tasks)} tasks")
            return {
                'batch_id': batch_id,
                'task_ids': [t['id'] for t in tasks],
                'status': 'submitted'
            }
        except Exception as e:
            logger.error(f"Failed to submit batch: {e}")
            return None
    
    def get_task_details(self, task_id: str) -> Optional[Dict[str, str]]:
        """Get task details from the handoff board"""
        tasks = self.scan_board()
        for task in tasks:
            if task['id'] == task_id:
                return task
        
        # If not in eligible tasks, search full board
        if not self.board_path.exists():
            return None
        
        content = self.board_path.read_text(encoding='utf-8')
        for line in content.split('\n'):
            if not line.strip().startswith('|'):
                continue
            
            parts = [p.strip() for p in line.split('|')]
            if len(parts) > 1 and parts[1] == task_id:
                return {
                    'id': task_id,
                    'title': parts[3] if len(parts) > 3 else '',
                    'priority': parts[2] if len(parts) > 2 else 'medium',
                    'status': parts[5] if len(parts) > 5 else 'queued',
                    'dependencies': parts[4] if len(parts) > 4 else '-'
                }
        
        return None

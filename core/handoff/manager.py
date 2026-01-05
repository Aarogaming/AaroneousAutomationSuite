import os
from pathlib import Path
from typing import List, Dict, Any, Tuple, Optional
from loguru import logger

class HandoffManager:
    """
    Manages the handoff process between agents using a Markdown-based task board.
    Automatically uses Batch API (50% cost savings) for bulk operations when enabled.
    """
    def __init__(self, config=None, task_board_path: str = "artifacts/handoff/ACTIVE_TASKS.md"):
        self.config = config
        self.task_board_path = Path(task_board_path)
        
        # Initialize batch processor if API keys are available
        self.batch_processor = None
        if config and hasattr(config, 'openai_api_key'):
            try:
                from core.managers.batch import BatchManager
                self.batch_processor = BatchManager(config)
                logger.info("✓ Batch API processor initialized - 50% cost savings enabled")
            except ImportError as e:
                logger.warning(f"BatchManager not available: {e}")
            except Exception as e:
                logger.warning(f"Batch processor initialization failed: {e}")
        
        # Try alternative locations if default doesn't exist
        if not self.task_board_path.exists():
            potential_paths = [
                Path(os.getcwd()) / "artifacts" / "handoff" / "ACTIVE_TASKS.md",
                Path("handoff/ACTIVE_TASKS.md") # Legacy fallback
            ]
            for p in potential_paths:
                if p.exists():
                    self.task_board_path = p
                    break
        
        if not self.task_board_path.exists():
            logger.warning(f"Task board not found at {task_board_path}")

    def parse_board(self) -> Tuple[List[str], List[Dict[str, Any]], Dict[str, str]]:
        """
        Parses the ACTIVE_TASKS.md file.
        Returns:
            - lines: All lines in the file
            - tasks: List of task dictionaries
            - status_map: Map of task_id -> status
        """
        if not self.task_board_path.exists():
            return [], [], {}

        with open(self.task_board_path, "r", encoding="utf-8") as f:
            lines = f.readlines()

        tasks = []
        status_map = {}
        
        # Simple Markdown table parser
        for i, line in enumerate(lines):
            if "|" in line and "AAS-" in line:
                parts = [p.strip() for p in line.split("|")]
                if len(parts) >= 9:
                    # | ID | Priority | Title | Depends On | Status | Assignee | Created | Updated |
                    task_id = parts[1]
                    status = parts[5]
                    
                    task = {
                        "index": i,
                        "id": task_id,
                        "priority": parts[2],
                        "title": parts[3],
                        "depends_on": parts[4],
                        "status": status,
                        "assignee": parts[6],
                        "created": parts[7],
                        "updated": parts[8],
                        "parts": parts
                    }
                    tasks.append(task)
                    status_map[task_id] = status

        return lines, tasks, status_map

    def get_blocked_tasks(self) -> List[Dict[str, Any]]:
        """Returns tasks that are queued but have unmet dependencies."""
        lines, tasks, status_map = self.parse_board()
        blocked = []
        
        for t in tasks:
            if t["status"].lower() == "queued" and t["depends_on"] != "-":
                dep_ids = [d.strip() for d in t["depends_on"].split(",")]
                unmet = [d for d in dep_ids if status_map.get(d) != "Done"]
                if unmet:
                    t["blocking_tasks"] = unmet
                    blocked.append(t)
        return blocked

    def complete_task(self, task_id: str) -> bool:
        """Marks a task as Done in the Markdown board."""
        lines, tasks, _ = self.parse_board()
        target = next((t for t in tasks if t["id"] == task_id), None)
        
        if not target:
            return False
            
        parts = target["parts"]
        parts[5] = "Done"
        import datetime
        parts[8] = datetime.datetime.now().strftime("%Y-%m-%d")
        
        lines[target["index"]] = " | ".join(parts) + "\n"
        
        with open(self.task_board_path, "w", encoding="utf-8") as f:
            f.writelines(lines)
        return True
    
    async def batch_analyze_queued_tasks(self, urgent: bool = False):
        """Analyze queued tasks using Batch API (50% cost savings)."""
        if not self.batch_processor:
            logger.error("Batch processor not initialized - check OPENAI_API_KEY")
            return {"status": "error", "message": "Batch processor not available"}
        
        lines, tasks, _ = self.parse_board()
        queued = [t for t in tasks if t["status"].lower() == "queued"]
        
        if not queued:
            logger.info("No queued tasks to analyze")
            return {"status": "success", "message": "No queued tasks found", "task_count": 0}
        
        # Smart routing: urgent or single task → sync, otherwise → batch
        if urgent or len(queued) == 1:
            logger.info(f"Using synchronous API (urgent={urgent}, count={len(queued)})")
            # Fall back to sync - would need separate implementation
            return {"status": "error", "message": "Sync analysis not implemented yet"}
        
        logger.info(f"📦 Analyzing {len(queued)} queued tasks via Batch API (50% savings)")
        
        # Build analysis requests
        requests = []
        for task in queued:
            prompt = f"""Analyze this task and provide:
1. Estimated complexity (Low/Medium/High)
2. Suggested priority adjustment (if any)
3. Potential blockers or dependencies
4. Recommended first step

Task: {task['id']} - {task['title']}
Current Priority: {task['priority']}
Status: {task['status']}"""
            
            requests.append({
                "custom_id": task['id'],
                "method": "POST",
                "url": "/v1/chat/completions",
                "body": {
                    "model": "gpt-4o-mini",
                    "messages": [{"role": "user", "content": prompt}],
                    "max_tokens": 1000
                }
            })
        
        # Submit batch job using BatchManager's submit_batch
        batch_id = await self.batch_processor.submit_batch(
            requests=requests,
            description=f"Analyze {len(queued)} queued tasks",
            metadata={"operation": "analyze_queued", "task_count": str(len(queued))}
        )
        
        return {
            "status": "submitted",
            "batch_id": batch_id,
            "task_count": len(queued),
            "tasks_analyzed": [t['id'] for t in queued],
            "message": f"Batch job created - check status with: .venv\\Scripts\\python.exe -c \"from core.managers.batch import BatchManager; from core.config.manager import load_config; bm = BatchManager(load_config()); print(bm.get_batch_status('{batch_id}'))\""
        }
    
    async def batch_classify_all_tasks(self):
        """Classify all tasks into categories using Batch API."""
        if not self.batch_processor:
            logger.error("Batch processor not initialized")
            return {"status": "error", "message": "Batch processor not available"}
        
        lines, tasks, _ = self.parse_board()
        
        if not tasks:
            return {"status": "success", "message": "No tasks to classify", "task_count": 0}
        
        logger.info(f"📦 Classifying {len(tasks)} tasks via Batch API")
        
        requests = []
        for task in tasks:
            prompt = f"""Classify this task into one category:
- Infrastructure: Setup, deployment, DevOps
- Feature: New functionality, enhancements
- Integration: Third-party services, APIs
- Documentation: Docs, guides, examples
- Bug: Fixes, debugging
- Research: Investigation, analysis

Task: {task['title']}
Provide ONLY the category name."""
            
            requests.append({
                "custom_id": f"classify_{task['id']}",
                "method": "POST",
                "url": "/v1/chat/completions",
                "body": {
                    "model": "gpt-4o-mini",
                    "messages": [{"role": "user", "content": prompt}],
                    "max_tokens": 50
                }
            })
        
        batch_id = await self.batch_processor.submit_batch(
            requests=requests,
            description=f"Classify {len(tasks)} tasks",
            metadata={"operation": "classify_tasks", "task_count": str(len(tasks))}
        )
        
        return {
            "status": "submitted",
            "batch_id": batch_id,
            "task_count": len(tasks)
        }
    
    async def batch_generate_task_descriptions(self):
        """Generate descriptions for tasks with missing descriptions."""
        if not self.batch_processor:
            return {"status": "error", "message": "Batch processor not available"}
        
        lines, tasks, _ = self.parse_board()
        needs_desc = [t for t in tasks if len(t.get('title', '')) < 30]  # Heuristic
        
        if not needs_desc:
            return {"status": "success", "message": "All tasks have descriptions"}
        
        logger.info(f"📦 Generating descriptions for {len(needs_desc)} tasks via Batch API")
        
        requests = []
        for task in needs_desc:
            prompt = f"""Generate a 2-3 sentence description for this task:
Title: {task['title']}
Provide technical details and expected outcome."""
            
            requests.append({
                "custom_id": f"desc_{task['id']}",
                "method": "POST",
                "url": "/v1/chat/completions",
                "body": {
                    "model": "gpt-4o-mini",
                    "messages": [{"role": "user", "content": prompt}],
                    "max_tokens": 500
                }
            })
        
        batch_id = await self.batch_processor.submit_batch(
            requests=requests,
            description=f"Generate descriptions for {len(needs_desc)} tasks",
            metadata={"operation": "generate_descriptions", "task_count": str(len(needs_desc))}
        )
        
        return {
            "status": "submitted",
            "batch_id": batch_id,
            "task_count": len(needs_desc)
        }

"""Batch Recycler - Recycles completed batch results back into task list"""

import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent.parent))

import json
import re
from typing import List, Dict, Any
from datetime import datetime
from loguru import logger

from core.task_manager import TaskManager
from core.db_manager import DatabaseManager
from core.config import AASConfig


class BatchRecycler:
    """Recycles batch results back into the task system"""

    def __init__(self):
        self.config = AASConfig()
        self.db = DatabaseManager(db_path="artifacts/aas.db")
        self.task_manager = TaskManager(self.config)
        self.results_dir = Path("artifacts/batch/results")
        self.processed_log = Path("artifacts/batch/recycled_batches.json")

    def load_processed_log(self) -> Dict[str, Any]:
        """Load the log of already processed batch files"""
        if self.processed_log.exists():
            with open(self.processed_log, "r") as f:
                return json.load(f)
        return {"recycled_batches": [], "total_tasks_created": 0, "last_recycled": None}

    def save_processed_log(self, log_data: Dict[str, Any]):
        """Save the processed batch log"""
        self.processed_log.parent.mkdir(parents=True, exist_ok=True)
        with open(self.processed_log, "w") as f:
            json.dump(log_data, f, indent=2)

    def extract_actionable_items(
        self, content: str, original_task_id: str
    ) -> List[Dict[str, str]]:
        """
        Extract actionable tasks from batch response content.

        Looks for:
        - Numbered lists with action items
        - Sections with implementation steps
        - TODO/FIXME patterns
        - Code examples that need implementation
        """
        items = []

        # Pattern 1: Implementation steps with "Step N:"
        step_pattern = (
            r"\*\*Step (\d+):\s*([^\n]+)\*\*\s*\n-\s*(.+?)(?=\n\n|\*\*Step|\Z)"
        )
        matches = re.finditer(step_pattern, content, re.IGNORECASE | re.DOTALL)

        for match in matches:
            step_num = match.group(1)
            step_title = match.group(2).strip()
            step_details = match.group(3).strip()

            # Clean up details
            details_lines = step_details.split("\n")
            cleaned_details = "\n".join(
                [line.strip() for line in details_lines if line.strip()]
            )

            items.append(
                {
                    "type": "implementation_step",
                    "title": f"Step {step_num}: {step_title}",
                    "description": f"**From Task {original_task_id}**\n\n{cleaned_details[:1000]}",
                    "parent_task": original_task_id,
                    "priority": "medium",
                }
            )

        # Pattern 2: Generic numbered steps (fallback if pattern 1 fails)
        if not items:
            generic_step_pattern = (
                r"(?:Step |(?:^\d+\.\s+)|(?:Phase \d+:))\s*([^\n]+?)(?:\n|$)"
            )
            generic_matches = re.finditer(generic_step_pattern, content, re.MULTILINE)

            for match in generic_matches:
                step_text = match.group(1).strip()
                if len(step_text) > 20 and len(step_text) < 200:
                    items.append(
                        {
                            "type": "implementation_step",
                            "title": f"Implement: {step_text}",
                            "description": f"**From Task {original_task_id}**\n\n{step_text}",
                            "parent_task": original_task_id,
                            "priority": "medium",
                        }
                    )

        # Pattern 3: TODO/FIXME items
        todo_pattern = r"(?:TODO|FIXME|TASK|ACTION):\s*(.+?)(?:\n|$)"
        todos = re.finditer(todo_pattern, content, re.IGNORECASE)

        for todo in todos:
            todo_text = todo.group(1).strip()
            if todo_text and len(todo_text) > 10:
                items.append(
                    {
                        "type": "todo",
                        "title": f"TODO: {todo_text[:80]}",
                        "description": f"**From Task {original_task_id}**\n\n{todo_text[:500]}",
                        "parent_task": original_task_id,
                        "priority": "high",
                    }
                )

        # Pattern 4: Sections marked as needing implementation
        impl_pattern = r"(?:requires? implementation|needs? to be implemented|should implement|must implement):\s*(.+?)(?:\n\n|\Z)"
        impl_matches = re.finditer(impl_pattern, content, re.IGNORECASE | re.DOTALL)

        for impl in impl_matches:
            impl_text = impl.group(1).strip()
            if len(impl_text) > 20 and len(impl_text) < 500:
                lines = impl_text.split("\n")
                title = lines[0][:100].strip()
                if title:
                    items.append(
                        {
                            "type": "required_implementation",
                            "title": f"Required: {title}",
                            "description": f"**From Task {original_task_id}**\n\n{impl_text[:1000]}",
                            "parent_task": original_task_id,
                            "priority": "high",
                        }
                    )

        # Pattern 5: Major section headers (Technical Requirements, Implementation, etc.)
        if len(items) < 3:  # Only use if we didn't find many items
            section_pattern = r"###\s+\d+\.\s+(.+?)(?:\n|$)"
            section_matches = re.finditer(section_pattern, content)

            for match in section_matches:
                section_title = match.group(1).strip()
                if section_title and len(section_title) < 100:
                    items.append(
                        {
                            "type": "major_section",
                            "title": f"Implement: {section_title}",
                            "description": f"**From Task {original_task_id}**\n\nMajor section that requires implementation: {section_title}",
                            "parent_task": original_task_id,
                            "priority": "medium",
                        }
                    )

        return items

    def parse_batch_result(self, result_file: Path) -> Dict[str, Any]:
        """Parse a batch result file and extract metadata"""
        with open(result_file, "r") as f:
            data = json.load(f)

        batch_id = data.get("batch_id", "unknown")
        task_id = data.get("task_id", "unknown")
        results = data.get("results", [])

        # Extract content from results
        all_content = []
        for result in results:
            if result.get("response"):
                response = result["response"]
                if response.get("body"):
                    body = response["body"]
                    if "choices" in body:
                        content = body["choices"][0]["message"]["content"]
                        all_content.append(content)

        combined_content = "\n\n".join(all_content)

        return {
            "batch_id": batch_id,
            "task_id": task_id,
            "content": combined_content,
            "result_count": len(results),
        }

    def recycle_batch(self, result_file: Path, dry_run: bool = False) -> int:
        """
        Recycle a batch result file back into task list.

        Args:
            result_file: Path to the batch result JSON file
            dry_run: If True, only show what would be created without creating tasks

        Returns:
            Number of tasks created
        """
        logger.info(f"Processing batch result: {result_file.name}")

        # Parse the result
        parsed = self.parse_batch_result(result_file)
        task_id = parsed["task_id"]
        content = parsed["content"]

        # Extract actionable items
        items = self.extract_actionable_items(content, task_id)

        if not items:
            logger.warning(f"No actionable items found in {result_file.name}")
            return 0

        logger.info(f"Found {len(items)} actionable items from {task_id}")

        # Create tasks
        created_count = 0
        created_task_ids = []

        for item in items:
            title = item["title"]
            description = (
                f"**Source:** Batch result from {task_id}\n\n{item['description']}"
            )
            priority = item.get("priority", "medium")

            if dry_run:
                logger.info(f"[DRY RUN] Would create: {title}")
            else:
                try:
                    new_task_id = self.task_manager.add_task(
                        priority=priority,
                        title=title,
                        description=description,
                        depends_on=task_id,  # Depend on the original task
                        task_type=item["type"],
                    )
                    created_task_ids.append(new_task_id)
                    created_count += 1
                    logger.success(f"Created task {new_task_id}: {title}")
                except Exception as e:
                    logger.error(f"Failed to create task '{title}': {e}")

        return created_count

    def recycle_all_pending(
        self, dry_run: bool = False, force: bool = False
    ) -> Dict[str, Any]:
        """
        Recycle all unprocessed batch result files.

        Args:
            dry_run: If True, show what would be created without creating
            force: If True, reprocess already-processed batches

        Returns:
            Summary statistics
        """
        if not self.results_dir.exists():
            logger.warning(f"Results directory not found: {self.results_dir}")
            return {"processed": 0, "tasks_created": 0, "errors": 0}

        # Load processed log
        log_data = self.load_processed_log()
        already_processed = set(log_data.get("recycled_batches", []))

        # Find all result files
        result_files = list(self.results_dir.glob("*_processed.json"))

        if not result_files:
            logger.info("No batch result files found")
            return {"processed": 0, "tasks_created": 0, "errors": 0}

        logger.info(f"Found {len(result_files)} batch result file(s)")

        stats = {"processed": 0, "tasks_created": 0, "errors": 0, "skipped": 0}

        for result_file in result_files:
            batch_id = result_file.stem.replace("_processed", "")

            # Skip if already processed (unless force)
            if batch_id in already_processed and not force:
                logger.info(f"Skipping already processed batch: {batch_id}")
                stats["skipped"] += 1
                continue

            try:
                tasks_created = self.recycle_batch(result_file, dry_run)
                stats["processed"] += 1
                stats["tasks_created"] += tasks_created

                # Mark as processed
                if not dry_run and batch_id not in already_processed:
                    already_processed.add(batch_id)
                    log_data["recycled_batches"].append(batch_id)
                    log_data["total_tasks_created"] = (
                        log_data.get("total_tasks_created", 0) + tasks_created
                    )
                    log_data["last_recycled"] = datetime.utcnow().isoformat()
                    self.save_processed_log(log_data)

            except Exception as e:
                logger.error(f"Error processing {result_file.name}: {e}")
                stats["errors"] += 1

        return stats


def main():
    """CLI entry point"""
    import argparse

    parser = argparse.ArgumentParser(description="Recycle batch results into task list")
    parser.add_argument(
        "--dry-run",
        action="store_true",
        help="Show what would be created without creating",
    )
    parser.add_argument(
        "--force", action="store_true", help="Reprocess already-processed batches"
    )
    parser.add_argument("--file", type=str, help="Process a specific batch result file")

    args = parser.parse_args()

    recycler = BatchRecycler()

    if args.file:
        # Process single file
        result_file = Path(args.file)
        if not result_file.exists():
            logger.error(f"File not found: {result_file}")
            return 1

        tasks_created = recycler.recycle_batch(result_file, args.dry_run)
        logger.info(
            f"\n{'[DRY RUN] Would create' if args.dry_run else 'Created'} {tasks_created} task(s)"
        )
    else:
        # Process all pending
        logger.info("🔄 Starting batch recycler...")
        stats = recycler.recycle_all_pending(args.dry_run, args.force)

        logger.info("\n" + "=" * 60)
        logger.info("📊 Recycling Summary:")
        logger.info(f"  Batches processed: {stats['processed']}")
        logger.info(f"  Tasks created: {stats['tasks_created']}")
        logger.info(f"  Skipped: {stats['skipped']}")
        logger.info(f"  Errors: {stats['errors']}")
        logger.info("=" * 60)

    return 0


if __name__ == "__main__":
    exit(main())

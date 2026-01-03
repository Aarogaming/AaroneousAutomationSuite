"""
Continuous Batch Monitor for AAS

Runs as a background daemon, continuously scanning the task board
and automatically submitting eligible tasks as batch jobs throughout the day.

Features:
- Real-time monitoring of task board changes
- Automatic batch submission on new eligible tasks
- Tracks submitted tasks to avoid duplicates
- Monitors batch completion and processes results
- Intelligent throttling and rate limiting
- Health checks and auto-recovery

Usage:
    python scripts/batch_monitor.py               # Start monitor
    python scripts/batch_monitor.py --dry-run     # Test mode
    python scripts/batch_monitor.py --interval 60 # Custom scan interval
"""

import sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).parent.parent))

import asyncio
import argparse
import json
import os
from datetime import datetime, timedelta
from typing import Dict, Set, List, Any, Optional
from loguru import logger
from core.config.manager import load_config
from core.handoff.manager import HandoffManager
from core.batch.processor import BatchProcessor
from core.batch.task_generator import TaskGenerator
from scripts.auto_batch import AutoBatcher


class BatchMonitor:
    """Continuous batch monitoring and submission service"""
    
    def __init__(
        self,
        config,
        scan_interval: int = 300,  # 5 minutes
        batch_check_interval: int = 1800,  # 30 minutes
        max_concurrent_batches: int = 5,
        max_tasks_per_batch: int = 20,
        dry_run: bool = False
    ):
        self.config = config
        self.scan_interval = scan_interval
        self.batch_check_interval = batch_check_interval
        self.max_concurrent_batches = max_concurrent_batches
        self.max_tasks_per_batch = max_tasks_per_batch
        self.dry_run = dry_run
        
        self.handoff = HandoffManager(config)
        self.batcher = AutoBatcher(config, dry_run=dry_run, max_tasks=max_tasks_per_batch)
        self.processor = BatchProcessor(config) if not dry_run else None
        self.linear = self.handoff.linear
        self.team_id = getattr(config, 'linear_team_id', None)
        self.task_generator = TaskGenerator(self.handoff, self.linear, config)
        
        # Tracking state
        self.state_file = Path("artifacts/batch/monitor_state.json")
        self.submitted_tasks: Set[str] = set()  # Task IDs currently in batches
        self.active_batches: Dict[str, Dict[str, Any]] = {}  # batch_id -> metadata
        self.completed_batches: Set[str] = set()
        self.last_board_hash: Optional[str] = None
        
        # Statistics
        self.stats = {
            'start_time': datetime.now().isoformat(),
            'scans_performed': 0,
            'batches_submitted': 0,
            'batches_completed': 0,
            'tasks_processed': 0,
            'total_cost_saved': 0.0
        }
        
        self._load_state()
        
    def _load_state(self):
        """Load persisted state from disk"""
        if self.state_file.exists():
            try:
                with open(self.state_file, 'r') as f:
                    state = json.load(f)
                    self.submitted_tasks = set(state.get('submitted_tasks', []))
                    self.active_batches = state.get('active_batches', {})
                    self.completed_batches = set(state.get('completed_batches', []))
                    self.stats.update(state.get('stats', {}))
                    logger.info(f"Loaded state: {len(self.submitted_tasks)} submitted tasks, "
                              f"{len(self.active_batches)} active batches")
            except Exception as e:
                logger.error(f"Failed to load state: {e}")
    
    def _save_state(self):
        """Persist state to disk"""
        self.state_file.parent.mkdir(parents=True, exist_ok=True)
        try:
            state = {
                'submitted_tasks': list(self.submitted_tasks),
                'active_batches': self.active_batches,
                'completed_batches': list(self.completed_batches),
                'stats': self.stats,
                'last_updated': datetime.now().isoformat()
            }
            with open(self.state_file, 'w') as f:
                json.dump(state, f, indent=2)
        except Exception as e:
            logger.error(f"Failed to save state: {e}")
    
    def _get_board_hash(self) -> str:
        """Get hash of current task board state"""
        if not os.path.exists(self.handoff.task_board_path):
            return ""
        with open(self.handoff.task_board_path, 'r', encoding='utf-8') as f:
            content = f.read()
        return str(hash(content))
    
    async def scan_for_eligible_tasks(self) -> List[Dict[str, Any]]:
        """Scan task board for new eligible tasks not yet submitted"""
        logger.debug("Scanning task board for eligible tasks...")
        
        # Archive completed tasks first
        archived_count = self.batcher.archive_done_tasks()
        if archived_count > 0:
            logger.info(f"📦 Archived {archived_count} completed tasks")
        
        # Check if board has changed
        current_hash = self._get_board_hash()
        if current_hash == self.last_board_hash:
            logger.debug("Task board unchanged since last scan")
            return []
        
        self.last_board_hash = current_hash
        self.stats['scans_performed'] += 1
        
        # Get all eligible tasks
        all_eligible = self.batcher.scan_board()
        
        # Filter out already submitted tasks
        new_eligible = [
            task for task in all_eligible
            if task['id'] not in self.submitted_tasks
        ]
        
        if new_eligible:
            logger.info(f"Found {len(new_eligible)} new eligible tasks (filtered {len(all_eligible) - len(new_eligible)} already submitted)")
            for task in new_eligible:
                logger.success(f"  ✅ NEW: {task['id']} ({task['title']})")
        else:
            logger.debug(f"No new eligible tasks (all {len(all_eligible)} already submitted)")
        
        return new_eligible
    
    async def submit_batch(self, tasks: List[Dict[str, Any]]) -> Optional[Dict[str, Any]]:
        """Submit a batch of tasks"""
        if not tasks:
            return None
        
        # Check concurrent batch limit
        if len(self.active_batches) >= self.max_concurrent_batches:
            logger.warning(f"Already at max concurrent batches ({self.max_concurrent_batches}), skipping submission")
            return None
        
        if self.dry_run:
            logger.info(f"DRY RUN: Would submit batch with {len(tasks)} tasks")
            for task in tasks:
                logger.info(f"  - {task['id']}: {task['title']}")
            return None
        
        try:
            # Submit batch
            result = await self.batcher.submit_batch(tasks)
            
            if result:
                # Track submission
                batch_id = result['batch_id']
                task_ids = result['task_ids']
                
                self.active_batches[batch_id] = {
                    'task_ids': task_ids,
                    'task_count': len(task_ids),
                    'submitted_at': datetime.now().isoformat(),
                    'status': result['status']
                }
                
                self.submitted_tasks.update(task_ids)
                self.stats['batches_submitted'] += 1
                self.stats['tasks_processed'] += len(task_ids)
                
                # Estimate cost savings (rough: $2.50 per task * 50% = $1.25 saved per task)
                estimated_savings = len(task_ids) * 1.25
                self.stats['total_cost_saved'] += estimated_savings
                
                self._save_state()
                
                logger.success(f"Batch {batch_id} submitted with {len(task_ids)} tasks")
                logger.info(f"Active batches: {len(self.active_batches)}/{self.max_concurrent_batches}")
                
                # Update Linear task statuses
                if self.linear and self.team_id:
                    await self._update_linear_batched(task_ids, batch_id)
                
                return result
        
        except Exception as e:
            logger.error(f"Failed to submit batch: {e}")
            return None
    
    async def _update_linear_batched(self, task_ids: List[str], batch_id: str):
        """
        Mark tasks as Batched/In Progress in Linear with batch info comment.
        """
        try:
            # Get workflow states
            states = self.linear.get_workflow_states(self.team_id)
            target_state = states.get('Batched') or states.get('In Progress')
            
            if not target_state:
                logger.warning("Could not find 'Batched' or 'In Progress' workflow state")
                return
            
            comment_body = f"""🤖 **Batch Processing Started**

This task has been submitted to OpenAI Batch API for processing.

- **Batch ID:** `{batch_id}`
- **Expected completion:** Within 24 hours
- **Cost savings:** 50% vs synchronous API

Results will be automatically posted when processing completes."""
            
            for task_id in task_ids:
                try:
                    # Get or create Linear issue
                    issue_id = self._get_or_create_linear_issue(task_id)
                    if not issue_id:
                        logger.warning(f"Could not get/create Linear issue for {task_id}, skipping")
                        continue
                    
                    # Update status
                    self.linear.update_task_status(issue_id, target_state)
                    
                    # Add comment
                    self.linear.add_comment(issue_id, comment_body)
                    
                    logger.success(f"Updated Linear task {task_id} to Batched status")
                    
                except Exception as e:
                    logger.error(f"Failed to update Linear task {task_id}: {e}")
        
        except Exception as e:
            logger.error(f"Failed to update Linear tasks: {e}")
    
    async def check_batch_status(self):
        """Check status of active batches and process completed ones"""
        if not self.active_batches or self.dry_run:
            return
        
        logger.debug(f"Checking status of {len(self.active_batches)} active batches...")
        
        completed_batch_ids = []
        
        for batch_id, metadata in list(self.active_batches.items()):
            try:
                # Get batch status
                batch_status = self.processor.manager.get_status(batch_id)
                
                old_status = metadata['status']
                new_status = batch_status['status']
                
                # Update status if changed
                if old_status != new_status:
                    logger.info(f"Batch {batch_id} status: {old_status} → {new_status}")
                    metadata['status'] = new_status
                
                # Check if completed
                if new_status == 'completed':
                    logger.success(f"Batch {batch_id} completed! Processing results...")
                    
                    # Process results and update Linear
                    await self._process_batch_results(batch_id, metadata)
                    
                    # Mark tasks as no longer submitted
                    task_ids = metadata['task_ids']
                    self.submitted_tasks -= set(task_ids)
                    
                    # Move to completed
                    completed_batch_ids.append(batch_id)
                    self.completed_batches.add(batch_id)
                    self.stats['batches_completed'] += 1
                    
                    logger.info(f"Tasks from batch now available for re-submission: {', '.join(task_ids)}")
                
                elif new_status in ['failed', 'expired', 'cancelled']:
                    logger.error(f"Batch {batch_id} ended with status: {new_status}")
                    
                    # Free up submitted tasks for retry
                    task_ids = metadata['task_ids']
                    self.submitted_tasks -= set(task_ids)
                    completed_batch_ids.append(batch_id)
            
            except Exception as e:
                logger.error(f"Error checking batch {batch_id}: {e}")
        
        # Remove completed batches from active
        for batch_id in completed_batch_ids:
            del self.active_batches[batch_id]
        
        if completed_batch_ids:
            self._save_state()
    
    async def _process_batch_results(self, batch_id: str, metadata: Dict[str, Any]):
        """
        Process completed batch results and update Linear tasks.
        
        Args:
            batch_id: Completed batch job ID
            metadata: Batch metadata with task_ids and other info
        """
        try:
            # Get batch results
            results = await self.processor.manager.get_results(batch_id)
            
            # Extract task responses
            task_responses = {}
            for result in results:
                custom_id = result.get('custom_id', '')
                response_data = result.get('response', {})
                
                # Extract AI response text
                if 'body' in response_data:
                    choices = response_data['body'].get('choices', [])
                    if choices:
                        message = choices[0].get('message', {})
                        content = message.get('content', '')
                        task_responses[custom_id] = content
            
            logger.info(f"Extracted {len(task_responses)} task responses from batch {batch_id}")
            
            # Save results to artifacts
            results_dir = Path("artifacts/batch/results")
            results_dir.mkdir(parents=True, exist_ok=True)
            results_file = results_dir / f"{batch_id}_processed.json"
            
            with open(results_file, 'w', encoding='utf-8') as f:
                json.dump({
                    'batch_id': batch_id,
                    'processed_at': datetime.now().isoformat(),
                    'task_ids': metadata['task_ids'],
                    'responses': task_responses
                }, f, indent=2)
            
            logger.success(f"Saved processed results to {results_file}")
            
            # Update Linear tasks
            if self.linear and self.team_id:
                await self._update_linear_completed(metadata['task_ids'], batch_id, task_responses, results_file)
            
            # Update statistics
            self.stats['tasks_processed'] += len(task_responses)
            estimated_cost_saved = len(task_responses) * 2.50  # ~$2.50 per task @ 50% savings
            self.stats['total_cost_saved'] += estimated_cost_saved
            
        except Exception as e:
            logger.error(f"Failed to process batch results for {batch_id}: {e}")
    
    def _get_or_create_linear_issue(self, task_id: str) -> Optional[str]:
        """
        Get Linear issue ID, creating the issue if it doesn't exist yet.
        """
        # Try to find existing issue
        issue_id = self.linear.get_issue_by_identifier(self.team_id, task_id)
        if issue_id:
            return issue_id
        
        # Issue doesn't exist - create it from handoff board
        logger.info(f"Creating Linear issue for {task_id} (doesn't exist yet)")
        
        try:
            task_details = self.batcher.get_task_details(task_id)
            if not task_details:
                logger.error(f"Could not find task {task_id} in handoff board")
                return None
            
            description = f"Auto-created from AAS handoff board for batch processing.\n\n**Priority:** {task_details.get('priority', 'medium')}\n**Status:** {task_details.get('status', 'queued')}"
            if task_details.get('dependencies') and task_details['dependencies'] != '-':
                description += f"\n**Dependencies:** {task_details['dependencies']}"
            
            issue_id = self.linear.create_issue(
                self.team_id,
                task_details['title'],
                description
            )
            
            if issue_id:
                logger.success(f"Created Linear issue for {task_id}: {issue_id}")
                return issue_id
            else:
                logger.error(f"Failed to create Linear issue for {task_id}")
                return None
                
        except Exception as e:
            logger.error(f"Failed to create Linear issue for {task_id}: {e}")
            return None

    
    async def _update_linear_completed(self, task_ids: List[str], batch_id: str, 
                                       responses: Dict[str, str], results_file: Path):
        """
        Update Linear tasks with batch completion info and AI responses.
        """
        try:
            # Get workflow states
            states = self.linear.get_workflow_states(self.team_id)
            target_state = states.get('In Review') or states.get('Done')
            
            if not target_state:
                logger.warning("Could not find 'In Review' or 'Done' workflow state")
                return
            
            for task_id in task_ids:
                try:
                    # Get or create Linear issue
                    issue_id = self._get_or_create_linear_issue(task_id)
                    if not issue_id:
                        logger.warning(f"Could not get/create Linear issue for {task_id}, skipping")
                        continue
                    
                    # Get AI response for this task
                    response_text = responses.get(task_id, "No response found")
                    
                    # Truncate if too long (Linear has character limits)
                    max_length = 15000
                    if len(response_text) > max_length:
                        response_text = response_text[:max_length] + "\n\n... (response truncated, see full results in artifacts)"
                    
                    # Create comment with results
                    comment_body = f"""✅ **Batch Processing Complete**

Batch `{batch_id}` has finished processing.

---

## AI Analysis Results

{response_text}

---

**Full results:** `{results_file.name}`
**Processing time:** Within 24 hours
**Cost savings:** ~50% vs synchronous API

Please review the recommendations and mark as Done if satisfactory."""
                    
                    # Update status to In Review
                    self.linear.update_task_status(issue_id, target_state)
                    
                    # Add comment with results
                    self.linear.add_comment(issue_id, comment_body)
                    
                    logger.success(f"Updated Linear task {task_id} with batch results")
                    
                except Exception as e:
                    logger.error(f"Failed to update Linear task {task_id}: {e}")
        
        except Exception as e:
            logger.error(f"Failed to update Linear tasks for batch {batch_id}: {e}")
    
    async def run_scan_cycle(self):
        """Run one scan cycle: check for new tasks and submit batch if needed"""
        try:
            # Scan for new eligible tasks
            new_tasks = await self.scan_for_eligible_tasks()
            
            if new_tasks:
                # Group into batches (respect max_tasks_per_batch)
                for i in range(0, len(new_tasks), self.max_tasks_per_batch):
                    batch_tasks = new_tasks[i:i + self.max_tasks_per_batch]
                    await self.submit_batch(batch_tasks)
                    
                    # Small delay between batch submissions
                    if i + self.max_tasks_per_batch < len(new_tasks):
                        await asyncio.sleep(5)
        
        except Exception as e:
            logger.error(f"Error in scan cycle: {e}")
    
    async def run_batch_check_cycle(self):
        """Run batch status check cycle"""
        try:
            await self.check_batch_status()
        except Exception as e:
            logger.error(f"Error in batch check cycle: {e}")
    
    async def run_task_generation_cycle(self):
        """
        Autonomous task generation cycle - runs every 6 hours.
        
        Reviews project progress, scans for issues, and creates tasks automatically.
        """
        try:
            # Check task count threshold: stop at 500, resume at <100
            total_tasks = self.task_generator.get_total_task_count()
            
            if total_tasks >= 500:
                logger.warning(f"🛑 Task creation SUSPENDED: {total_tasks}/500 tasks on board")
                logger.info("Will resume when count drops below 100")
                logger.info("=" * 60)
                return
            elif total_tasks >= 400:
                logger.warning(f"⚠️ Approaching task limit: {total_tasks}/500 tasks")
            elif total_tasks >= 100:
                logger.info(f"📊 Task board status: {total_tasks} tasks (normal operation)")
            else:
                logger.success(f"✅ Task board healthy: {total_tasks} tasks")

            logger.info("=" * 60)
            logger.info("AUTONOMOUS TASK GENERATION CYCLE")
            logger.info("=" * 60)
            
            all_suggestions = []
            
            # 1. Review project progress
            logger.info("Phase 1: Project Progress Review")
            progress_suggestions = await self.task_generator.review_project_progress()
            all_suggestions.extend(progress_suggestions)
            logger.info(f"  → {len(progress_suggestions)} suggestions from progress review")
            
            # 2. Scan for issues
            logger.info("Phase 2: Issue Scanning")
            issue_suggestions = await self.task_generator.scan_for_issues()
            all_suggestions.extend(issue_suggestions)
            logger.info(f"  → {len(issue_suggestions)} suggestions from issue scan")
            
            # 3. Identify improvements
            logger.info("Phase 3: Improvement Analysis")
            improvement_suggestions = await self.task_generator.suggest_improvements()
            all_suggestions.extend(improvement_suggestions)
            logger.info(f"  → {len(improvement_suggestions)} suggestions from improvement analysis")
            
            logger.info(f"\nTotal suggestions: {len(all_suggestions)}")
            
            # Create tasks (only high priority ones automatically, rest in dry run mode for review)
            if all_suggestions:
                high_priority = [s for s in all_suggestions if s.get('priority') == 'high']
                other_priority = [s for s in all_suggestions if s.get('priority') != 'high']
                
                if high_priority:
                    logger.info(f"\nCreating {len(high_priority)} high-priority tasks...")
                    created = await self.task_generator.create_tasks(high_priority, dry_run=self.dry_run)
                    logger.success(f"Created {len(created)} high-priority tasks")
                
                if other_priority:
                    logger.info(f"\nLogging {len(other_priority)} medium/low-priority suggestions for review...")
                    for suggestion in other_priority:
                        logger.info(f"  • [{suggestion.get('priority')}] {suggestion.get('title')}")
            
            logger.info("=" * 60)
            logger.info(f"Next task generation cycle in 6 hours")
            logger.info("=" * 60)
            
            # Wait 6 hours before next cycle
            await asyncio.sleep(21600)  # 6 hours
            
        except Exception as e:
            logger.error(f"Error in task generation cycle: {e}")
            # On error, wait 1 hour before retry
            await asyncio.sleep(3600)
    
    def print_status(self):
        """Print current monitor status"""
        uptime = datetime.now() - datetime.fromisoformat(self.stats['start_time'])
        
        logger.info("=" * 60)
        logger.info("BATCH MONITOR STATUS")
        logger.info("=" * 60)
        logger.info(f"Uptime: {uptime}")
        logger.info(f"Scans performed: {self.stats['scans_performed']}")
        logger.info(f"Active batches: {len(self.active_batches)}/{self.max_concurrent_batches}")
        logger.info(f"Submitted tasks: {len(self.submitted_tasks)}")
        logger.info(f"Batches submitted: {self.stats['batches_submitted']}")
        logger.info(f"Batches completed: {self.stats['batches_completed']}")
        logger.info(f"Tasks processed: {self.stats['tasks_processed']}")
        logger.info(f"Estimated cost saved: ${self.stats['total_cost_saved']:.2f}")
        
        if self.active_batches:
            logger.info("\nActive Batches:")
            for batch_id, meta in self.active_batches.items():
                logger.info(f"  {batch_id}: {meta['status']} ({len(meta['task_ids'])} tasks)")
        
        logger.info("=" * 60)
    
    async def run(self):
        """Main monitoring loop"""
        logger.info("=" * 60)
        logger.info("BATCH MONITOR STARTING")
        logger.info("=" * 60)
        logger.info(f"Scan interval: {self.scan_interval}s")
        logger.info(f"Batch check interval: {self.batch_check_interval}s")
        logger.info(f"Max concurrent batches: {self.max_concurrent_batches}")
        logger.info(f"Max tasks per batch: {self.max_tasks_per_batch}")
        logger.info(f"Dry run: {self.dry_run}")
        logger.info("=" * 60)
        
        # Initial status
        self.print_status()
        
        # Create background tasks
        scan_task = None
        batch_check_task = None
        task_generation_task = None
        status_task = None
        
        try:
            while True:
                # Start scan cycle if not running
                if scan_task is None or scan_task.done():
                    scan_task = asyncio.create_task(self.run_scan_cycle())
                
                # Start batch check cycle if not running
                if batch_check_task is None or batch_check_task.done():
                    batch_check_task = asyncio.create_task(self.run_batch_check_cycle())
                
                # Start task generation cycle if not running (runs every 6 hours)
                if task_generation_task is None or task_generation_task.done():
                    task_generation_task = asyncio.create_task(self.run_task_generation_cycle())
                
                # Print status every hour
                if status_task is None or status_task.done():
                    async def status_loop():
                        await asyncio.sleep(3600)  # 1 hour
                        self.print_status()
                    status_task = asyncio.create_task(status_loop())
                
                # Wait for scan interval
                await asyncio.sleep(self.scan_interval)
        
        except KeyboardInterrupt:
            logger.info("\nShutdown requested...")
            
            # Cancel background tasks
            for task in [scan_task, batch_check_task, status_task]:
                if task and not task.done():
                    task.cancel()
            
            # Final status
            self.print_status()
            self._save_state()
            
            logger.info("Batch monitor stopped")
        
        except Exception as e:
            logger.error(f"Fatal error in monitor: {e}")
            self._save_state()
            raise


async def main():
    parser = argparse.ArgumentParser(description='Continuous batch monitoring service')
    parser.add_argument('--dry-run', action='store_true', help='Test mode (no actual submissions)')
    parser.add_argument('--interval', type=int, default=300, help='Scan interval in seconds (default: 300 = 5 min)')
    parser.add_argument('--batch-check', type=int, default=1800, help='Batch check interval in seconds (default: 1800 = 30 min)')
    parser.add_argument('--max-batches', type=int, default=5, help='Max concurrent batches (default: 5)')
    parser.add_argument('--max-tasks', type=int, default=20, help='Max tasks per batch (default: 20)')
    parser.add_argument('--debug', action='store_true', help='Enable debug logging')
    args = parser.parse_args()
    
    if args.debug:
        logger.remove()
        logger.add(lambda msg: print(msg, end=''), level="DEBUG")
    
    # Load config
    config = load_config()
    
    if not config.openai_api_key:
        logger.error("OpenAI API key not configured. Set OPENAI_API_KEY in .env")
        return 1
    
    # Create and run monitor
    monitor = BatchMonitor(
        config,
        scan_interval=args.interval,
        batch_check_interval=args.batch_check,
        max_concurrent_batches=args.max_batches,
        max_tasks_per_batch=args.max_tasks,
        dry_run=args.dry_run
    )
    
    await monitor.run()
    
    return 0


if __name__ == '__main__':
    exit(asyncio.run(main()))

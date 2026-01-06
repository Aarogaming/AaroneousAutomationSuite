"""Batch Workflow Orchestrator - Full automation of batch lifecycle"""
import sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).parent.parent))

from datetime import datetime
from loguru import logger

from scripts.batch_auto_clear import BatchAutoClear
from scripts.batch_recycler import BatchRecycler


class BatchWorkflowOrchestrator:
    """
    Orchestrates the full batch processing lifecycle:
    1. Check for completed batches
    2. Retrieve results
    3. Recycle results into task list
    4. Archive old files
    5. Generate reports
    """
    
    def __init__(self):
        self.auto_clear = BatchAutoClear()
        self.recycler = BatchRecycler()
    
    def run_full_workflow(self, dry_run: bool = False) -> dict:
        """
        Run the complete batch workflow.
        
        Steps:
        1. Auto-clear batch backlog (check status, retrieve completed)
        2. Recycle retrieved results into task list
        3. Generate comprehensive report
        """
        logger.info("🚀 Starting Batch Workflow Orchestrator...")
        logger.info(f"Mode: {'DRY RUN' if dry_run else 'LIVE'}")
        logger.info("")
        
        workflow_start = datetime.utcnow()
        
        # Step 1: Auto-clear batch backlog
        logger.info("=" * 60)
        logger.info("STEP 1: Auto-Clear Batch Backlog")
        logger.info("=" * 60)
        
        clear_result = self.auto_clear.auto_clear_backlog(dry_run)
        clear_report = self.auto_clear.generate_report(clear_result)
        print(clear_report)
        
        # Step 2: Recycle batch results into task list
        logger.info("")
        logger.info("=" * 60)
        logger.info("STEP 2: Recycle Results into Task List")
        logger.info("=" * 60)
        
        recycle_stats = self.recycler.recycle_all_pending(dry_run, force=False)
        
        logger.info("")
        logger.info("📋 Recycling Summary:")
        logger.info(f"  Batches processed: {recycle_stats['processed']}")
        logger.info(f"  Tasks created: {recycle_stats['tasks_created']}")
        logger.info(f"  Skipped: {recycle_stats['skipped']}")
        logger.info(f"  Errors: {recycle_stats['errors']}")
        
        # Step 3: Generate comprehensive report
        workflow_end = datetime.utcnow()
        duration = (workflow_end - workflow_start).total_seconds()
        
        logger.info("")
        logger.info("=" * 60)
        logger.info("🎉 WORKFLOW COMPLETE")
        logger.info("=" * 60)
        logger.info(f"Duration: {duration:.2f}s")
        logger.info(f"Mode: {'DRY RUN' if dry_run else 'LIVE'}")
        logger.info("")
        logger.info("Summary:")
        logger.info(f"  ✓ Batches completed: {clear_result['stats']['batches_completed']}")
        logger.info(f"  ✓ Results retrieved: {clear_result['stats']['batches_retrieved']}")
        logger.info(f"  ✓ Tasks created: {recycle_stats['tasks_created']}")
        logger.info(f"  ✓ Files archived: {clear_result['stats']['results_archived']}")
        logger.info("=" * 60)
        
        return {
            "duration": duration,
            "clear_result": clear_result,
            "recycle_stats": recycle_stats
        }


def main():
    """CLI entry point"""
    import argparse
    
    parser = argparse.ArgumentParser(
        description="Orchestrate full batch processing workflow",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
  # Dry run (preview what would happen)
  python scripts/batch_workflow.py --dry-run
  
  # Live run (make actual changes)
  python scripts/batch_workflow.py
  
  # Schedule with Task Scheduler or cron for automation:
  # Windows: Task Scheduler -> Run daily at 2 AM
  # Linux: crontab -e -> 0 2 * * * /path/to/python scripts/batch_workflow.py
        """
    )
    
    parser.add_argument(
        "--dry-run",
        action="store_true",
        help="Preview what would happen without making changes"
    )
    
    args = parser.parse_args()
    
    orchestrator = BatchWorkflowOrchestrator()
    
    try:
        orchestrator.run_full_workflow(args.dry_run)
        return 0
    except Exception as e:
        logger.error(f"Workflow failed: {e}")
        return 1


if __name__ == "__main__":
    exit(main())

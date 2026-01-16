"""Batch Auto-Clear - Automatically clear batch backlog when criteria are met"""

import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent.parent))

import json
from datetime import datetime, timedelta
from typing import Dict, Any, List
from loguru import logger

from openai import OpenAI
from core.config import AASConfig


class BatchAutoClear:
    """Automatically process and clear batch backlog based on criteria"""

    def __init__(self):
        self.config = AASConfig()
        self.client = OpenAI(api_key=self.config.openai_api_key.get_secret_value())
        self.monitor_state_path = Path("artifacts/batch/monitor_state.json")
        self.results_dir = Path("artifacts/batch/results")

        # Configurable criteria
        self.criteria = {
            "max_pending_age_hours": 24,  # Auto-retrieve batches older than 24h
            "max_active_batches": 10,  # Trigger cleanup if more than 10 active
            "min_completion_rate": 0.5,  # At least 50% of batches should be complete
            "auto_retrieve_completed": True,  # Auto-retrieve completed batches
            "archive_old_results": True,  # Archive results older than 30 days
            "archive_age_days": 30,
        }

    def load_monitor_state(self) -> Dict[str, Any]:
        """Load batch monitor state"""
        if not self.monitor_state_path.exists():
            return {
                "submitted_tasks": [],
                "active_batches": {},
                "completed_batches": [],
                "stats": {},
            }

        with open(self.monitor_state_path, "r") as f:
            return json.load(f)

    def save_monitor_state(self, state: Dict[str, Any]):
        """Save batch monitor state"""
        state["last_updated"] = datetime.utcnow().isoformat()
        with open(self.monitor_state_path, "w") as f:
            json.dump(state, f, indent=2)

    def check_batch_status(self, batch_id: str) -> Dict[str, Any]:
        """Check status of a specific batch"""
        try:
            batch = self.client.batches.retrieve(batch_id)
            return {
                "id": batch_id,
                "status": batch.status,
                "created_at": batch.created_at,
                "completed_at": batch.completed_at,
                "request_counts": {
                    "total": batch.request_counts.total,
                    "completed": batch.request_counts.completed,
                    "failed": batch.request_counts.failed,
                },
                "output_file_id": (
                    batch.output_file_id if hasattr(batch, "output_file_id") else None
                ),
            }
        except Exception as e:
            logger.error(f"Failed to check batch {batch_id}: {e}")
            return None

    def retrieve_batch_results(self, batch_id: str, output_file_id: str) -> bool:
        """Retrieve and save batch results"""
        try:
            logger.info(f"Retrieving results for batch {batch_id}...")

            # Download results
            result_content = self.client.files.content(output_file_id)
            result_text = result_content.text

            # Parse results
            results = []
            for line in result_text.strip().split("\n"):
                if line:
                    results.append(json.loads(line))

            # Save to file
            output_path = self.results_dir / f"{batch_id}_processed.json"
            output_path.parent.mkdir(parents=True, exist_ok=True)

            with open(output_path, "w") as f:
                json.dump(
                    {
                        "batch_id": batch_id,
                        "retrieved_at": datetime.utcnow().isoformat(),
                        "results": results,
                    },
                    f,
                    indent=2,
                )

            logger.success(f"Saved results to {output_path}")
            return True

        except Exception as e:
            logger.error(f"Failed to retrieve batch results: {e}")
            return False

    def archive_old_results(self) -> int:
        """Archive old batch results"""
        if not self.criteria["archive_old_results"]:
            return 0

        archive_dir = Path("artifacts/batch/archive")
        archive_dir.mkdir(parents=True, exist_ok=True)

        cutoff_date = datetime.utcnow() - timedelta(
            days=self.criteria["archive_age_days"]
        )
        archived_count = 0

        if not self.results_dir.exists():
            return 0

        for result_file in self.results_dir.glob("*_processed.json"):
            # Check file age
            file_mtime = datetime.fromtimestamp(result_file.stat().st_mtime)

            if file_mtime < cutoff_date:
                # Move to archive
                archive_path = archive_dir / result_file.name
                result_file.rename(archive_path)
                logger.info(f"Archived old result: {result_file.name}")
                archived_count += 1

        return archived_count

    def evaluate_criteria(self, state: Dict[str, Any]) -> Dict[str, bool]:
        """
        Evaluate whether batch backlog clearing criteria are met.

        Returns dict of criterion -> passed/failed
        """
        results = {}
        active_batches = state.get("active_batches", {})
        completed_batches = state.get("completed_batches", [])

        # Criterion 1: Max active batches
        results["max_active_batches"] = (
            len(active_batches) <= self.criteria["max_active_batches"]
        )

        # Criterion 2: Completion rate
        total = len(active_batches) + len(completed_batches)
        if total > 0:
            completion_rate = len(completed_batches) / total
            results["completion_rate"] = (
                completion_rate >= self.criteria["min_completion_rate"]
            )
        else:
            results["completion_rate"] = True  # No batches = no problem

        # Criterion 3: Old pending batches
        old_batches = []
        cutoff_time = datetime.utcnow() - timedelta(
            hours=self.criteria["max_pending_age_hours"]
        )

        for batch_id, batch_info in active_batches.items():
            submitted_at = datetime.fromisoformat(
                batch_info.get("submitted_at", datetime.utcnow().isoformat())
            )
            if submitted_at < cutoff_time:
                old_batches.append(batch_id)

        results["no_old_pending"] = len(old_batches) == 0
        results["old_batches"] = old_batches

        return results

    def auto_clear_backlog(self, dry_run: bool = False) -> Dict[str, Any]:
        """
        Automatically clear batch backlog based on criteria.

        Steps:
        1. Check all active batches for completion
        2. Retrieve completed batch results
        3. Update monitor state
        4. Archive old results
        5. Report statistics
        """
        logger.info("🧹 Starting batch backlog auto-clear...")

        state = self.load_monitor_state()
        active_batches = state.get("active_batches", {})

        stats = {
            "batches_checked": 0,
            "batches_completed": 0,
            "batches_retrieved": 0,
            "batches_failed": 0,
            "results_archived": 0,
        }

        # Step 1: Check all active batches
        logger.info(f"Checking {len(active_batches)} active batch(es)...")

        newly_completed = []

        for batch_id, _batch_info in list(active_batches.items()):
            stats["batches_checked"] += 1
            batch_status = self.check_batch_status(batch_id)

            if not batch_status:
                stats["batches_failed"] += 1
                continue

            logger.info(f"Batch {batch_id}: {batch_status['status']}")

            # Step 2: Handle completed batches
            if batch_status["status"] == "completed":
                stats["batches_completed"] += 1

                if self.criteria["auto_retrieve_completed"]:
                    if not dry_run:
                        # Retrieve results
                        if batch_status["output_file_id"]:
                            success = self.retrieve_batch_results(
                                batch_id, batch_status["output_file_id"]
                            )
                            if success:
                                stats["batches_retrieved"] += 1
                                newly_completed.append(batch_id)
                    else:
                        logger.info(f"[DRY RUN] Would retrieve results for {batch_id}")
                        newly_completed.append(batch_id)

            elif batch_status["status"] in ["failed", "expired", "cancelled"]:
                logger.warning(
                    f"Batch {batch_id} has terminal status: {batch_status['status']}"
                )
                stats["batches_failed"] += 1
                if not dry_run:
                    newly_completed.append(batch_id)  # Remove from active

        # Step 3: Update monitor state
        if not dry_run and newly_completed:
            for batch_id in newly_completed:
                if batch_id in active_batches:
                    del active_batches[batch_id]
                if batch_id not in state["completed_batches"]:
                    state["completed_batches"].append(batch_id)

            # Update stats
            state["stats"]["batches_completed"] = len(state["completed_batches"])
            state["stats"]["tasks_processed"] = state["stats"].get(
                "tasks_processed", 0
            ) + len(newly_completed)

            self.save_monitor_state(state)
            logger.success(
                f"Updated monitor state with {len(newly_completed)} newly completed batch(es)"
            )

        # Step 4: Archive old results
        if not dry_run:
            archived = self.archive_old_results()
            stats["results_archived"] = archived
            if archived > 0:
                logger.success(f"Archived {archived} old result file(s)")

        # Step 5: Evaluate criteria
        criteria_results = self.evaluate_criteria(state)

        return {"stats": stats, "criteria": criteria_results, "state": state}

    def generate_report(self, clear_result: Dict[str, Any]) -> str:
        """Generate human-readable report"""
        stats = clear_result["stats"]
        criteria = clear_result["criteria"]

        report = []
        report.append("=" * 60)
        report.append("📊 BATCH BACKLOG AUTO-CLEAR REPORT")
        report.append("=" * 60)
        report.append("")
        report.append("Statistics:")
        report.append(f"  ✓ Batches checked: {stats['batches_checked']}")
        report.append(f"  ✓ Newly completed: {stats['batches_completed']}")
        report.append(f"  ✓ Results retrieved: {stats['batches_retrieved']}")
        report.append(f"  ✗ Failed batches: {stats['batches_failed']}")
        report.append(f"  📦 Results archived: {stats['results_archived']}")
        report.append("")
        report.append("Criteria Status:")

        for criterion, passed in criteria.items():
            if criterion == "old_batches":
                continue
            icon = "✓" if passed else "✗"
            report.append(f"  {icon} {criterion}: {'PASS' if passed else 'FAIL'}")

        if "old_batches" in criteria and criteria["old_batches"]:
            report.append(f"  ⚠️  Old pending batches: {len(criteria['old_batches'])}")
            for batch_id in criteria["old_batches"][:5]:  # Show first 5
                report.append(f"      - {batch_id}")

        report.append("=" * 60)

        return "\n".join(report)


def main():
    """CLI entry point"""
    import argparse

    parser = argparse.ArgumentParser(description="Auto-clear batch backlog")
    parser.add_argument(
        "--dry-run",
        action="store_true",
        help="Show what would happen without making changes",
    )
    parser.add_argument("--report", action="store_true", help="Generate report only")

    args = parser.parse_args()

    auto_clear = BatchAutoClear()

    if args.report:
        # Just evaluate criteria without clearing
        state = auto_clear.load_monitor_state()
        criteria = auto_clear.evaluate_criteria(state)

        print("\n📋 Current Batch Backlog Status:")
        print(f"  Active batches: {len(state.get('active_batches', {}))}")
        print(f"  Completed batches: {len(state.get('completed_batches', []))}")
        print("\nCriteria:")
        for criterion, passed in criteria.items():
            if criterion == "old_batches":
                continue
            icon = "✓" if passed else "✗"
            print(f"  {icon} {criterion}: {'PASS' if passed else 'FAIL'}")

        if criteria.get("old_batches"):
            print(f"\n⚠️  Old pending batches ({len(criteria['old_batches'])}):")
            for batch_id in criteria["old_batches"]:
                print(f"    - {batch_id}")
    else:
        # Run auto-clear
        result = auto_clear.auto_clear_backlog(args.dry_run)
        report = auto_clear.generate_report(result)
        print("\n" + report)

    return 0


if __name__ == "__main__":
    exit(main())

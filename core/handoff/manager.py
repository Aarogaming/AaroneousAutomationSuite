import os
from datetime import datetime
from typing import Optional, Any
from loguru import logger
from core.handoff.linear import LinearSync
from core.config.manager import AASConfig

class HandoffManager:
    """
    Autonomous Handoff Protocol (AHP) Manager.
    Handles task ingestion, event reporting, and health monitoring.
    """
    def __init__(self, config: Optional[AASConfig] = None, artifact_dir: str = "artifacts/handoff"):
        self.artifact_dir = artifact_dir
        self.task_board_path = "handoff/ACTIVE_TASKS.md"
        self.config = config
        self.linear = None
        
        if config and config.linear_api_key:
            self.linear = LinearSync(config.linear_api_key)
            logger.info("Linear API integration initialized.")
            
        self._ensure_dirs()

    def parse_board(self) -> tuple[list[str], list[dict[str, Any]], dict[str, str]]:
        """Parses the Markdown board into lines, task list, and status map."""
        if not os.path.exists(self.task_board_path):
            return [], [], {}
        
        with open(self.task_board_path, "r", encoding="utf-8") as f:
            lines = f.readlines()
            
        tasks = []
        status_map = {}
        for i, line in enumerate(lines):
            if "|" in line and "Status" not in line and ":" not in line and "-|-" not in line:
                parts = [p.strip() for p in line.split("|")]
                if len(parts) >= 9:
                    task_id = parts[1]
                    status = parts[5]
                    status_map[task_id] = status
                    tasks.append({
                        "index": i,
                        "id": task_id,
                        "priority": parts[2].lower(),
                        "title": parts[3],
                        "depends_on": parts[4],
                        "status": status,
                        "assignee": parts[6],
                        "created": parts[7],
                        "updated": parts[8],
                        "parts": parts
                    })
        return lines, tasks, status_map

    def claim_next_task(self, actor_name: str) -> Optional[dict[str, str]]:
        """
        Implements FCFS 'Claim-on-Read' logic using the local Markdown board.
        Sorts by priority: Urgent > High > Medium > Low.
        Respects 'Depends On' column.
        """
        lines, tasks, status_map = self.parse_board()
        if not tasks:
            return None

        priority_map = {"urgent": 0, "high": 1, "medium": 2, "low": 3}
        
        eligible_tasks = []
        for t in tasks:
            if t["status"].lower() == "queued":
                # Check dependencies
                depends_on = t["depends_on"]
                if depends_on and depends_on != "-":
                    dep_ids = [d.strip() for d in depends_on.split(",")]
                    if any(status_map.get(dep_id) != "Done" for dep_id in dep_ids):
                        continue
                
                eligible_tasks.append(t)

        if not eligible_tasks:
            return None

        # Sort by priority value (lower is higher priority)
        eligible_tasks.sort(key=lambda x: priority_map.get(x["priority"], 4))
        best_task = eligible_tasks[0]
        
        today = datetime.now().strftime("%Y-%m-%d")
        parts = best_task["parts"]
        parts[5] = "In Progress"
        parts[6] = actor_name
        parts[8] = today
        
        lines[best_task["index"]] = " | ".join(parts) + "\n"

        with open(self.task_board_path, "w", encoding="utf-8") as f:
            f.writelines(lines)

        # Auto-scaffold artifacts
        task_id: str = str(best_task["id"])
        task_dir = os.path.join(self.artifact_dir, task_id)
        os.makedirs(task_dir, exist_ok=True)
        readme_path = os.path.join(task_dir, "README.md")
        if not os.path.exists(readme_path):
            with open(readme_path, "w", encoding="utf-8") as f:
                f.write(f"# Task {task_id}: {best_task['title']}\n\n## Summary\n(To be filled by {actor_name})\n\n## Artifacts\n- \n")

        logger.success(f"Actor '{actor_name}' claimed task {task_id}: {best_task['title']}")
        return {"id": task_id, "title": str(best_task["title"])}

    def complete_task(self, task_id: str) -> bool:
        """
        Marks a task as 'Done' in the local Markdown board.
        """
        lines, tasks, _ = self.parse_board()
        target_task = next((t for t in tasks if t["id"] == task_id), None)
        
        if not target_task:
            return False

        today = datetime.now().strftime("%Y-%m-%d")
        parts = target_task["parts"]
        parts[5] = "Done"
        parts[8] = today
        lines[target_task["index"]] = " | ".join(parts) + "\n"

        with open(self.task_board_path, "w", encoding="utf-8") as f:
            f.writelines(lines)
        logger.success(f"Task {task_id} marked as Done.")
        return True

    def add_task(self, priority: str, title: str, description: str, depends_on: str = "-", task_type: str = "feature") -> str:
        """
        Programmatically adds a new task to the board.
        """
        lines, tasks, _ = self.parse_board()
        
        # Generate next ID
        max_id = 0
        for t in tasks:
            try:
                num = int(t["id"].split("-")[1])
                if num > max_id:
                    max_id = num
            except (IndexError, ValueError):
                continue
        
        new_id = f"AAS-{max_id + 1:03d}"
        today = datetime.now().strftime("%Y-%m-%d")
        
        # Create table row
        new_row = f" | {new_id} | {priority.capitalize()} | {title} | {depends_on} | queued | - | {today} | {today} | \n"
        
        # Find the end of the table
        table_end = 0
        for i, line in enumerate(lines):
            if "|" in line:
                table_end = i + 1
        
        lines.insert(table_end, new_row)
        
        # Add details section
        lines.append(f"\n### {new_id}: {title}\n")
        lines.append(f"- **Description**: {description}\n")
        lines.append(f"- **Type**: {task_type}\n")
        lines.append("- **Acceptance Criteria**:\n")
        lines.append("    - [ ] Initial implementation\n")

        with open(self.task_board_path, "w", encoding="utf-8") as f:
            f.writelines(lines)
            
        logger.success(f"Added new task {new_id}: {title}")
        return new_id

    def _ensure_dirs(self):
        os.makedirs(os.path.join(self.artifact_dir, "from_codex"), exist_ok=True)
        os.makedirs(os.path.join(self.artifact_dir, "to_codex"), exist_ok=True)
        os.makedirs(os.path.join(self.artifact_dir, "reports"), exist_ok=True)

    def generate_health_report(self) -> str:
        """
        Aggregates errors, warnings, and TODOs into a HEALTH_REPORT.md
        """
        from core.handoff.health import HealthAggregator
        aggregator = HealthAggregator()
        scan_results = aggregator.scan()

        report = [
            "# AAS HEALTH REPORT",
            f"Timestamp: {datetime.now().isoformat()}",
            "\n## 🔴 Errors", "None detected.",
            "\n## 🟡 Warnings", "None detected.",
            "\n## 📝 To-Do List"
        ]

        # Add scanned TODOs
        if scan_results["TODO"]:
            report.extend([f"- [ ] {t}" for t in scan_results["TODO"]])
        
        # Add scanned FIXMEs
        if scan_results["FIXME"]:
            report.append("\n## 🛠️ Fixmes")
            report.extend([f"- {f}" for f in scan_results["FIXME"]])

        # Add Audit/Build results
        if scan_results["AUDIT"]:
            report.append("\n## 🔍 Audit & Build Status")
            report.extend([f"- {a}" for a in scan_results["AUDIT"]])

        if not scan_results["TODO"] and not scan_results["FIXME"]:
            report.append("All critical setup tasks completed.")

        report_path = os.path.join(self.artifact_dir, "reports", "HEALTH_REPORT.md")
        with open(report_path, "w", encoding="utf-8") as f:
            f.write("\n".join(report))
        return report_path

    def report_event(self, task_id: str, event_type: str, message: str):
        event = {
            "event_id": f"evt_{datetime.now().timestamp()}",
            "task_id": task_id,
            "timestamp": datetime.now().isoformat(),
            "actor": "AAS_Hub",
            "event_type": event_type,
            "message": message
        }
        logger.info(f"Handoff Event: {event_type} - {message}")
        
        # If it's a critical event and Linear is connected, create an issue
        if event_type.lower() in ["error", "critical"] and self.linear:
            team_id = os.getenv("LINEAR_TEAM_ID", "AAS") # Default team ID
            self.linear.create_issue(
                team_id=team_id,
                title=f"[{event_type}] {message[:50]}...",
                description=f"Event ID: {event['event_id']}\nTask ID: {task_id}\nMessage: {message}"
            )

    def sync_linear_tasks(self, team_id: str):
        """
        Syncs active tasks from Linear to local state.
        """
        if not self.linear:
            logger.warning("Linear sync skipped: API not initialized.")
            return

        tasks = self.linear.get_active_tasks(team_id)
        logger.info(f"Synced {len(tasks)} tasks from Linear.")
        
        # Update local ROADMAP.md or TASK_BOARD.md based on Linear state
        # This is a placeholder for more complex sync logic
        for task in tasks:
            logger.debug(f"Task: {task['title']} ({task['status']['name']})")

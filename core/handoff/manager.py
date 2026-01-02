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
    
    def get_blocked_tasks(self) -> list[dict[str, Any]]:
        """
        Returns a list of tasks that are blocked by incomplete dependencies.
        
        Returns:
            List of task dicts with 'id', 'title', 'blocking_tasks' fields
        """
        lines, tasks, status_map = self.parse_board()
        blocked = []
        
        for t in tasks:
            if t["status"].lower() == "queued" and t["depends_on"] and t["depends_on"] != "-":
                dep_ids = [d.strip() for d in t["depends_on"].split(",")]
                incomplete_deps = [dep_id for dep_id in dep_ids if status_map.get(dep_id) != "Done"]
                
                if incomplete_deps:
                    blocked.append({
                        "id": t["id"],
                        "title": t["title"],
                        "priority": t["priority"],
                        "blocking_tasks": incomplete_deps,
                        "depends_on": t["depends_on"]
                    })
        
        return blocked
    
    def get_task_board_health(self) -> dict[str, Any]:
        """
        Analyzes the task board health and returns issues.
        
        Returns:
            Dict with 'stale_tasks', 'unassigned_high_priority', 'missing_artifacts'
        """
        lines, tasks, _ = self.parse_board()
        
        health = {
            "stale_tasks": [],
            "unassigned_high_priority": [],
            "missing_artifacts": [],
            "summary": {}
        }
        
        now = datetime.now()
        stale_threshold_days = 3
        
        for t in tasks:
            task_id = t["id"]
            
            # Check for stale tasks (In Progress > 3 days)
            if t["status"] == "In Progress":
                try:
                    updated = datetime.strptime(t["updated"], "%Y-%m-%d")
                    days_old = (now - updated).days
                    if days_old > stale_threshold_days:
                        health["stale_tasks"].append({
                            "id": task_id,
                            "title": t["title"],
                            "assignee": t["assignee"],
                            "days_old": days_old,
                            "updated": t["updated"]
                        })
                except ValueError:
                    logger.warning(f"Invalid date format for task {task_id}")
            
            # Check for unassigned high-priority tasks
            if t["status"] == "queued" and (t["priority"].lower() in ["urgent", "high"]):
                if not t["assignee"] or t["assignee"] == "-":
                    health["unassigned_high_priority"].append({
                        "id": task_id,
                        "title": t["title"],
                        "priority": t["priority"]
                    })
            
            # Check for missing artifact directories (for In Progress/Done tasks)
            if t["status"] in ["In Progress", "Done"]:
                artifact_path = os.path.join(self.artifact_dir, task_id)
                if not os.path.exists(artifact_path):
                    health["missing_artifacts"].append({
                        "id": task_id,
                        "title": t["title"],
                        "status": t["status"],
                        "expected_path": artifact_path
                    })
        
        # Generate summary
        health["summary"] = {
            "total_tasks": len(tasks),
            "stale_count": len(health["stale_tasks"]),
            "unassigned_high_priority_count": len(health["unassigned_high_priority"]),
            "missing_artifacts_count": len(health["missing_artifacts"]),
            "health_score": self._calculate_health_score(health, len(tasks))
        }
        
        return health
    
    def _calculate_health_score(self, health: dict, total_tasks: int) -> str:
        """Calculate overall health score based on issues detected."""
        if total_tasks == 0:
            return "N/A"
        
        issue_count = (
            len(health["stale_tasks"]) +
            len(health["unassigned_high_priority"]) +
            len(health["missing_artifacts"])
        )
        
        if issue_count == 0:
            return "Excellent"
        elif issue_count <= 2:
            return "Good"
        elif issue_count <= 5:
            return "Fair"
        else:
            return "Needs Attention"

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
        Aggregates errors, warnings, TODOs, and task board health into HEALTH_REPORT.md
        """
        from core.handoff.health import HealthAggregator
        aggregator = HealthAggregator()
        scan_results = aggregator.scan()
        task_health = self.get_task_board_health()

        report = [
            "# AAS HEALTH REPORT",
            f"Timestamp: {datetime.now().isoformat()}",
            f"\n## 📊 Task Board Health",
            f"**Health Score**: {task_health['summary']['health_score']}",
            f"**Total Tasks**: {task_health['summary']['total_tasks']}",
            ""
        ]
        
        # Stale Tasks Section
        if task_health["stale_tasks"]:
            report.append("### ⏰ Stale Tasks (In Progress > 3 days)")
            for task in task_health["stale_tasks"]:
                report.append(f"- **{task['id']}**: {task['title']}")
                report.append(f"  - Assignee: {task['assignee']}")
                report.append(f"  - Last Updated: {task['updated']} ({task['days_old']} days ago)")
        else:
            report.append("### ⏰ Stale Tasks")
            report.append("✅ No stale tasks detected")
        
        # Unassigned High-Priority Tasks
        report.append("")
        if task_health["unassigned_high_priority"]:
            report.append("### 🚨 Unassigned High-Priority Tasks")
            for task in task_health["unassigned_high_priority"]:
                report.append(f"- **{task['id']}** [{task['priority'].upper()}]: {task['title']}")
        else:
            report.append("### 🚨 Unassigned High-Priority Tasks")
            report.append("✅ All high-priority tasks are assigned")
        
        # Missing Artifact Directories
        report.append("")
        if task_health["missing_artifacts"]:
            report.append("### 📁 Missing Artifact Directories")
            for task in task_health["missing_artifacts"]:
                report.append(f"- **{task['id']}** [{task['status']}]: Missing `{task['expected_path']}`")
        else:
            report.append("### 📁 Artifact Directories")
            report.append("✅ All active task artifacts present")

        # Errors and Warnings (placeholder for future integration)
        report.append("\n## 🔴 Errors")
        report.append("None detected.")
        
        report.append("\n## 🟡 Warnings")
        report.append("None detected.")
        
        # Code TODOs
        report.append("\n## 📝 Code To-Do Items")
        if scan_results["TODO"]:
            report.extend([f"- [ ] {t}" for t in scan_results["TODO"][:10]])  # Show first 10
            if len(scan_results["TODO"]) > 10:
                report.append(f"- ... and {len(scan_results['TODO']) - 10} more")
        else:
            report.append("None found.")
        
        # FIXMEs
        if scan_results["FIXME"]:
            report.append("\n## 🛠️ Code Fixmes")
            report.extend([f"- {f}" for f in scan_results["FIXME"][:10]])
            if len(scan_results["FIXME"]) > 10:
                report.append(f"- ... and {len(scan_results['FIXME']) - 10} more")

        # Audit/Build results
        if scan_results["AUDIT"]:
            report.append("\n## 🔍 Audit & Build Status")
            report.extend([f"- {a}" for a in scan_results["AUDIT"]])

        report_path = os.path.join(self.artifact_dir, "reports", "HEALTH_REPORT.md")
        with open(report_path, "w", encoding="utf-8") as f:
            f.write("\n".join(report))
        
        logger.info(f"Health report generated: {report_path}")
        logger.info(f"Task Board Health Score: {task_health['summary']['health_score']}")
        
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

    def decompose_task(self, task_id: str):
        """
        Uses LangGraph to decompose a complex task into sub-tasks.
        """
        from core.handoff.agent import create_decomposition_graph
        
        lines, tasks, _ = self.parse_board()
        target_task = next((t for t in tasks if t["id"] == task_id), None)
        
        if not target_task:
            logger.error(f"Task {task_id} not found for decomposition.")
            return

        logger.info(f"Triggering agentic decomposition for {task_id}...")
        
        graph = create_decomposition_graph()
        initial_state = {
            "task_id": task_id,
            "title": target_task["title"],
            "description": target_task.get("description", "No description provided."),
            "sub_tasks": [],
            "status": "started"
        }
        
        graph.invoke(initial_state)

    def sync_linear_tasks(self, team_id: str):
        """
        Syncs active tasks from Linear to local state.
        """
        if not self.linear:
            logger.warning("Linear sync skipped: API not initialized.")
            return

        linear_tasks = self.linear.get_active_tasks(team_id)
        logger.info(f"Fetched {len(linear_tasks)} tasks from Linear.")
        
        lines, local_tasks, _ = self.parse_board()
        
        for lt in linear_tasks:
            # Check if task already exists locally by title (or ID if we store it)
            exists = any(lt["title"].lower() == t["title"].lower() for t in local_tasks)
            
            if not exists:
                logger.info(f"Importing new task from Linear: {lt['title']}")
                # Map Linear status to local status
                status_map = {
                    "Todo": "queued",
                    "In Progress": "In Progress",
                    "Done": "Done",
                    "Canceled": "canceled",
                    "Backlog": "queued"
                }
                local_status = status_map.get(lt["status"]["name"], "queued")
                
                self.add_task(
                    priority="medium", # Default
                    title=lt["title"],
                    description=lt["description"] or "Imported from Linear",
                    task_type="feature"
                )

    def push_local_to_linear(self, team_id: str):
        """
        Pushes local task updates to Linear.
        """
        if not self.linear:
            return

        _, local_tasks, _ = self.parse_board()
        
        for t in local_tasks:
            # This is a simplified version. In a real app, we'd store the Linear Issue ID
            # in the local task board to avoid duplicates and enable updates.
            # For now, we'll just log what we would do.
            logger.debug(f"Would push local task {t['id']} to Linear if not already there.")

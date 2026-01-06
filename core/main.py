import sys
import argparse
from datetime import datetime
from pathlib import Path
from typing import Any, Dict, List, Optional
from loguru import logger

# Add project root to path
sys.path.insert(0, str(Path(__file__).parent.parent))

from core.managers import ManagerHub
from core.handoff_manager import HandoffManager


def _normalize_status(value: str) -> str:
    return value.lower().replace("_", " ").strip()


def _load_tasks() -> tuple[list[str], list[dict], dict[str, str]]:
    handoff = HandoffManager()
    return handoff.parse_board()


def _filter_available(tasks: list[dict], status_map: dict[str, str]) -> list[dict]:
    available = []
    for task in tasks:
        if _normalize_status(task["status"]) != "queued":
            continue
        deps = task.get("depends_on", "-")
        if deps and deps != "-":
            dep_ids = [d.strip() for d in deps.split(",")]
            unmet = [
                d for d in dep_ids
                if _normalize_status(status_map.get(d, "")) != "done"
            ]
            if unmet:
                continue
        available.append(task)
    return available


def _print_task_table(tasks: list[dict]) -> None:
    for task in tasks:
        print(f"{task['id']} | {task['priority']} | {task['status']} | {task['title']}")


def _create_task(lines: list[str], tasks: list[dict], title: str, priority: str, description: str) -> str:
    max_id = 0
    for task in tasks:
        task_id = task.get("id", "")
        if "-" in task_id:
            try:
                max_id = max(max_id, int(task_id.split("-")[1]))
            except ValueError:
                continue

    new_id = f"AAS-{max_id + 1:03d}"
    today = datetime.now().strftime("%Y-%m-%d")
    priority_cap = priority.capitalize()
    new_row = f" | {new_id} | {priority_cap} | {title} | - | queued | - | {today} | {today} | \n"

    table_end = 0
    for i, line in enumerate(lines):
        if "|" in line:
            table_end = i + 1
    lines.insert(table_end, new_row)

    lines.append(f"\n### {new_id}: {title}\n")
    lines.append(f"- **Description**: {description or '-'}\n")
    lines.append("- **Type**: feature\n")
    lines.append("- **Acceptance Criteria**:\n")
    lines.append("    - [ ] Initial implementation\n")

    board_path = HandoffManager().task_board_path
    board_path.write_text("".join(lines), encoding="utf-8")
    return new_id


def _start_task(lines: list[str], tasks: list[dict], status_map: dict[str, str], task_id: str, assignee: str) -> str:
    target = next((t for t in tasks if t["id"] == task_id), None)
    if not target:
        return f"Task {task_id} not found"

    deps = target.get("depends_on", "-")
    if deps and deps != "-":
        dep_ids = [d.strip() for d in deps.split(",")]
        unmet = [
            d for d in dep_ids
            if _normalize_status(status_map.get(d, "")) != "done"
        ]
        if unmet:
            return f"Task {task_id} is blocked by: {', '.join(unmet)}"

    parts = target["parts"]
    parts[5] = "In Progress"
    parts[6] = assignee
    parts[8] = datetime.now().strftime("%Y-%m-%d")
    lines[target["index"]] = " | ".join(parts) + "\n"
    board_path = HandoffManager().task_board_path
    board_path.write_text("".join(lines), encoding="utf-8")
    return f"Task {task_id} started by {assignee}"


def run_cli(args: list[str]) -> int:
    parser = argparse.ArgumentParser(prog="aas")
    subparsers = parser.add_subparsers(dest="command")

    task_parser = subparsers.add_parser("task")
    task_sub = task_parser.add_subparsers(dest="task_command")

    task_sub.add_parser("available")

    task_list = task_sub.add_parser("list")
    task_list.add_argument("--status", dest="status")
    task_list.add_argument("--priority", dest="priority")

    task_show = task_sub.add_parser("show")
    task_show.add_argument("task_id")

    task_create = task_sub.add_parser("create")
    task_create.add_argument("title", nargs="+")
    task_create.add_argument("--priority", default="Medium")
    task_create.add_argument("--description", default="")

    task_start = task_sub.add_parser("start")
    task_start.add_argument("task_id")
    task_start.add_argument("assignee")

    subparsers.add_parser("board")
    subparsers.add_parser("blocked")

    parsed = parser.parse_args(args)
    lines, tasks, status_map = _load_tasks()

    if parsed.command == "task":
        if parsed.task_command == "available":
            print("AVAILABLE TASKS")
            available = _filter_available(tasks, status_map)
            if not available:
                print("No available tasks.")
            else:
                _print_task_table(available)
            return 0

        if parsed.task_command == "list":
            print("TASKS")
            filtered = tasks
            if parsed.status:
                status_norm = _normalize_status(parsed.status)
                filtered = [t for t in filtered if _normalize_status(t["status"]) == status_norm]
            if parsed.priority:
                priority_norm = parsed.priority.lower()
                filtered = [t for t in filtered if t["priority"].lower() == priority_norm]
            if not filtered:
                print("No tasks match filters.")
            else:
                _print_task_table(filtered)
            return 0

        if parsed.task_command == "show":
            task = next((t for t in tasks if t["id"] == parsed.task_id), None)
            if not task:
                print(f"Task {parsed.task_id} not found")
                return 0
            print("TASK DETAILS")
            print(f"ID: {task['id']}")
            print(f"Title: {task['title']}")
            print(f"Priority: {task['priority']}")
            print(f"Status: {task['status']}")
            print(f"Assignee: {task['assignee']}")
            print(f"Depends On: {task['depends_on']}")
            print(f"Created: {task['created']}")
            print(f"Updated: {task['updated']}")
            return 0

        if parsed.task_command == "create":
            title = " ".join(parsed.title)
            new_id = _create_task(lines, tasks, title, parsed.priority, parsed.description)
            print(f"Created task {new_id}")
            return 0

        if parsed.task_command == "start":
            message = _start_task(lines, tasks, status_map, parsed.task_id, parsed.assignee)
            print(message)
            return 0

    if parsed.command == "board":
        print("AAS ACTIVE TASK BOARD")
        print("Summary:")
        print(f"Total Tasks: {len(tasks)}")
        return 0

    if parsed.command == "blocked":
        handoff = HandoffManager()
        blocked = handoff.get_blocked_tasks()
        if not blocked:
            print("No blocked tasks.")
            return 0
        print("BLOCKED TASKS")
        for task in blocked:
            blocking = ", ".join(task.get("blocking_tasks", []))
            print(f"{task['id']} - {task['title']} (blocked by {blocking})")
        return 0

    parser.print_help()
    return 1


def main() -> None:
    """Main entry point for AAS Hub or CLI."""
    if len(sys.argv) > 1:
        sys.exit(run_cli(sys.argv[1:]))

    logger.info("Starting Aaroneous Automation Suite (AAS) Hub...")

    try:
        hub = ManagerHub.create()
        health = hub.get_health_summary()
        overall = health.get("overall_status", health.get("status", "unknown"))
        logger.info(f"System Health: {overall}")

        # In a real scenario, this would start the web server, IPC server, etc.
        logger.info("AAS Hub is running. Press Ctrl+C to stop.")

    except Exception as e:
        logger.critical(f"Failed to start AAS Hub: {e}")
        sys.exit(1)


if __name__ == "__main__":
    main()

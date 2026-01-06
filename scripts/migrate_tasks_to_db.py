"""
Migration Script - Markdown to Database

Migrates tasks from handoff/ACTIVE_TASKS.md to the SQLAlchemy database.
"""

import sys
from pathlib import Path

# Add parent directory to path
sys.path.insert(0, str(Path(__file__).parent.parent))

from loguru import logger
from core.config import AASConfig
from core.db_manager import DatabaseManager
from core.db_models import Task, TaskStatus, TaskPriority
from core.handoff_manager import HandoffManager


def map_priority(p: str) -> TaskPriority:
    p = p.lower()
    if p == "urgent": return TaskPriority.URGENT
    if p == "high": return TaskPriority.HIGH
    if p == "low": return TaskPriority.LOW
    return TaskPriority.MEDIUM


def map_status(s: str) -> TaskStatus:
    s = s.lower()
    if s == "in progress": return TaskStatus.IN_PROGRESS
    if s == "done": return TaskStatus.DONE
    if s == "blocked": return TaskStatus.BLOCKED
    if s == "failed": return TaskStatus.FAILED
    return TaskStatus.QUEUED


def migrate():
    logger.info("Starting migration: Markdown -> Database")
    
    # Initialize config with dummy key if missing for CLI
    import os
    if not os.getenv("OPENAI_API_KEY"):
        os.environ["OPENAI_API_KEY"] = "sk-dummy-key-for-migration"
        
    config = AASConfig() # type: ignore
    db = DatabaseManager(db_path="artifacts/aas.db")
    db.create_tables()
    handoff = HandoffManager(config)
    
    lines, tasks, _ = handoff.parse_board()
    logger.info(f"Found {len(tasks)} tasks in ACTIVE_TASKS.md")
    
    with db.get_session() as session:
        for t in tasks:
            # Check if task already exists
            existing = session.query(Task).filter(Task.id == t["id"]).first()
            if existing:
                logger.debug(f"Task {t['id']} already exists in DB, updating...")
                task = existing
            else:
                logger.debug(f"Creating new task {t['id']} in DB")
                task = Task(id=t["id"])
                session.add(task)
            
            task.title = t["title"]
            task.priority = map_priority(t["priority"])
            task.status = map_status(t["status"])
            task.assignee = t["assignee"] if t["assignee"] != "-" else None
            
            # Handle dependencies
            if t["depends_on"] and t["depends_on"] != "-":
                task.dependencies = [d.strip() for d in t["depends_on"].split(",")]
            else:
                task.dependencies = []
            
            # Set timestamps if available
            try:
                from datetime import datetime
                task.created_at = datetime.strptime(t["created"], "%Y-%m-%d")
                task.updated_at = datetime.strptime(t["updated"], "%Y-%m-%d")
            except Exception:
                pass
    
    logger.success("Migration complete!")


if __name__ == "__main__":
    migrate()

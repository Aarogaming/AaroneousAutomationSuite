"""
HandoffManager integration with database layer.

Extends HandoffManager to persist tasks, events, and artifacts to the database.
"""

from typing import List, Optional
from datetime import datetime
from loguru import logger

from core.db_manager import get_db_manager
from core.db_models import Task, Event, TaskStatus, TaskPriority, EventType
from core.db_repositories import TaskRepository, TaskExecutionRepository, EventRepository


class DatabaseHandoffMixin:
    """
    Mixin to add database persistence to HandoffManager.
    
    Usage:
        class HandoffManager(DatabaseHandoffMixin):
            def __init__(self, ...):
                super().__init__(...)
                self.init_database()
    """
    
    def init_database(self, db_path: str = "artifacts/aas.db") -> None:
        """Initialize database connection."""
        self.db = get_db_manager(db_path=db_path)
        logger.info("Database integration initialized")
    
    def sync_task_to_db(
        self,
        task_id: str,
        title: str,
        priority: str = "medium",
        status: str = "queued",
        assignee: Optional[str] = None,
        dependencies: Optional[List[str]] = None
    ) -> None:
        """
        Sync a task from ACTIVE_TASKS.md to database.
        
        Args:
            task_id: Task ID (e.g., "AAS-001")
            title: Task title
            priority: Task priority ("urgent", "high", "medium", "low")
            status: Task status ("queued", "in_progress", "done", etc.)
            assignee: Assigned agent
            dependencies: List of task IDs this depends on
        """
        priority_map = {
            "urgent": TaskPriority.URGENT,
            "high": TaskPriority.HIGH,
            "medium": TaskPriority.MEDIUM,
            "low": TaskPriority.LOW
        }
        
        status_map = {
            "queued": TaskStatus.QUEUED,
            "in progress": TaskStatus.IN_PROGRESS,
            "done": TaskStatus.DONE,
            "blocked": TaskStatus.BLOCKED,
            "failed": TaskStatus.FAILED
        }
        
        with self.db.get_session() as session:
            existing = TaskRepository.get_by_id(session, task_id)
            
            if existing is not None:
                # Update existing task
                existing.title = title # type: ignore
                existing.priority = priority_map.get(priority.lower(), TaskPriority.MEDIUM) # type: ignore
                existing.status = status_map.get(status.lower(), TaskStatus.QUEUED) # type: ignore
                existing.assignee = assignee # type: ignore
                existing.dependencies = dependencies or [] # type: ignore
                session.commit()
                logger.debug(f"Updated task {task_id} in database")
            else:
                # Create new task
                TaskRepository.create(
                    session,
                    task_id=task_id,
                    title=title,
                    priority=priority_map.get(priority.lower(), TaskPriority.MEDIUM),
                    dependencies=dependencies
                )
                
                if status.lower() != "queued":
                    TaskRepository.update_status(
                        session,
                        task_id,
                        status_map.get(status.lower(), TaskStatus.QUEUED),
                        assignee=assignee
                    )
                logger.info(f"Created task {task_id} in database")
    
    def report_event_to_db(
        self,
        task_id: Optional[str],
        event_type: str,
        message: str,
        source: Optional[str] = None,
        context_data: Optional[dict] = None
    ) -> None:
        """
        Report an event to the database.
        
        Args:
            task_id: Associated task ID (optional)
            event_type: Event type ("info", "warning", "error", "critical")
            message: Event message
            source: Source component
            context_data: Additional context
        """
        event_type_map = {
            "info": EventType.INFO,
            "warning": EventType.WARNING,
            "error": EventType.ERROR,
            "critical": EventType.CRITICAL
        }
        
        with self.db.get_session() as session:
            EventRepository.create(
                session,
                event_type=event_type_map.get(event_type.lower(), EventType.INFO),
                message=message,
                task_id=task_id,
                source=source,
                context_data=context_data
            )
        
        logger.debug(f"Logged {event_type} event to database")
    
    def start_task_execution(
        self,
        task_id: str,
        agent: str
    ) -> int:
        """
        Log start of task execution.
        
        Args:
            task_id: Task ID
            agent: Agent name
        
        Returns:
            Execution ID for later completion
        """
        with self.db.get_session() as session:
            execution = TaskExecutionRepository.create(
                session,
                task_id=task_id,
                agent=agent
            )
            logger.info(f"Started execution {execution.id} for {task_id} by {agent}")
            return int(execution.id) # type: ignore
    
    def complete_task_execution(
        self,
        execution_id: int,
        status: str,
        output: Optional[str] = None,
        error_message: Optional[str] = None,
        artifacts: Optional[List[str]] = None
    ) -> None:
        """
        Log completion of task execution.
        
        Args:
            execution_id: Execution ID from start_task_execution
            status: Execution status ("success", "failure", "partial")
            output: Execution output
            error_message: Error message if failed
            artifacts: List of artifact paths
        """
        with self.db.get_session() as session:
            TaskExecutionRepository.complete(
                session,
                execution_id=execution_id,
                status=status,
                output=output,
                error_message=error_message,
                artifacts=artifacts
            )
        
        logger.info(f"Completed execution {execution_id} with status {status}")
    
    def get_task_history(self, task_id: str) -> List[dict]:
        """
        Get execution history for a task.
        
        Args:
            task_id: Task ID
        
        Returns:
            List of execution records
        """
        with self.db.get_session() as session:
            executions = TaskExecutionRepository.get_by_task(session, task_id)
            return [
                {
                    "id": int(ex.id), # type: ignore
                    "agent": str(ex.agent),
                    "status": str(ex.status),
                    "started_at": ex.started_at.isoformat() if ex.started_at is not None else None,
                    "completed_at": ex.completed_at.isoformat() if ex.completed_at is not None else None,
                    "duration_seconds": ex.duration_seconds,
                    "output": ex.output,
                    "artifacts": ex.artifacts
                }
                for ex in executions
            ]
    
    def get_recent_events(self, limit: int = 50) -> List[dict]:
        """
        Get recent events from database.
        
        Args:
            limit: Maximum number of events to return
        
        Returns:
            List of event records
        """
        with self.db.get_session() as session:
            events = EventRepository.get_recent(session, limit=limit)
            return [
                {
                    "id": ev.id,
                    "task_id": ev.task_id,
                    "event_type": ev.event_type.value,
                    "message": ev.message,
                    "source": ev.source,
                    "created_at": ev.created_at.isoformat(),
                    "context_data": ev.context_data
                }
                for ev in events
            ]

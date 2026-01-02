"""
Database repository layer providing high-level database operations.

Repositories abstract database queries and provide a clean API for
working with database models using Pydantic schemas.
"""

from typing import List, Optional
from datetime import datetime
from sqlalchemy.orm import Session
from loguru import logger

from .models import (
    Task, TaskExecution, Event, Plugin, ConfigEntry,
    TaskStatus, TaskPriority, EventType, PluginStatus
)
from .manager import get_db_manager


class TaskRepository:
    """Repository for Task model operations."""
    
    @staticmethod
    def create(
        session: Session,
        task_id: str,
        title: str,
        priority: TaskPriority = TaskPriority.MEDIUM,
        description: Optional[str] = None,
        dependencies: Optional[List[str]] = None
    ) -> Task:
        """Create a new task."""
        task = Task(
            id=task_id,
            title=title,
            description=description,
            priority=priority,
            dependencies=dependencies or []
        )
        session.add(task)
        session.commit()
        session.refresh(task)
        logger.info(f"Created task: {task_id}")
        return task
    
    @staticmethod
    def get_by_id(session: Session, task_id: str) -> Optional[Task]:
        """Get task by ID."""
        return session.query(Task).filter(Task.id == task_id).first()
    
    @staticmethod
    def get_all(session: Session) -> List[Task]:
        """Get all tasks."""
        return session.query(Task).all()
    
    @staticmethod
    def get_by_status(session: Session, status: TaskStatus) -> List[Task]:
        """Get tasks by status."""
        return session.query(Task).filter(Task.status == status).all()
    
    @staticmethod
    def get_by_assignee(session: Session, assignee: str) -> List[Task]:
        """Get tasks by assignee."""
        return session.query(Task).filter(Task.assignee == assignee).all()
    
    @staticmethod
    def update_status(
        session: Session,
        task_id: str,
        status: TaskStatus,
        assignee: Optional[str] = None
    ) -> Optional[Task]:
        """Update task status and optionally assignee."""
        task = TaskRepository.get_by_id(session, task_id)
        if task:
            task.status = status
            if assignee:
                task.assignee = assignee
            if status == TaskStatus.IN_PROGRESS and not task.started_at:
                task.started_at = datetime.utcnow()
            if status == TaskStatus.DONE:
                task.completed_at = datetime.utcnow()
            session.commit()
            session.refresh(task)
            logger.info(f"Updated task {task_id} status to {status.value}")
        return task
    
    @staticmethod
    def delete(session: Session, task_id: str) -> bool:
        """Delete a task."""
        task = TaskRepository.get_by_id(session, task_id)
        if task:
            session.delete(task)
            session.commit()
            logger.info(f"Deleted task: {task_id}")
            return True
        return False


class TaskExecutionRepository:
    """Repository for TaskExecution model operations."""
    
    @staticmethod
    def create(
        session: Session,
        task_id: str,
        agent: str,
        status: str = "in_progress"
    ) -> TaskExecution:
        """Create a new task execution."""
        execution = TaskExecution(
            task_id=task_id,
            agent=agent,
            status=status
        )
        session.add(execution)
        session.commit()
        session.refresh(execution)
        logger.info(f"Created execution for task {task_id} by {agent}")
        return execution
    
    @staticmethod
    def complete(
        session: Session,
        execution_id: int,
        status: str,
        output: Optional[str] = None,
        error_message: Optional[str] = None,
        artifacts: Optional[List[str]] = None
    ) -> Optional[TaskExecution]:
        """Complete a task execution."""
        execution = session.query(TaskExecution).filter(
            TaskExecution.id == execution_id
        ).first()
        
        if execution:
            execution.status = status
            execution.completed_at = datetime.utcnow()
            execution.duration_seconds = int(
                (execution.completed_at - execution.started_at).total_seconds()
            )
            execution.output = output
            execution.error_message = error_message
            execution.artifacts = artifacts or []
            session.commit()
            session.refresh(execution)
            logger.info(f"Completed execution {execution_id} with status {status}")
        return execution
    
    @staticmethod
    def get_by_task(session: Session, task_id: str) -> List[TaskExecution]:
        """Get all executions for a task."""
        return session.query(TaskExecution).filter(
            TaskExecution.task_id == task_id
        ).order_by(TaskExecution.started_at.desc()).all()


class EventRepository:
    """Repository for Event model operations."""
    
    @staticmethod
    def create(
        session: Session,
        event_type: EventType,
        message: str,
        task_id: Optional[str] = None,
        source: Optional[str] = None,
        stack_trace: Optional[str] = None,
        context_data: Optional[dict] = None
    ) -> Event:
        """Create a new event."""
        event = Event(
            event_type=event_type,
            message=message,
            task_id=task_id,
            source=source,
            stack_trace=stack_trace,
            context_data=context_data
        )
        session.add(event)
        session.commit()
        session.refresh(event)
        logger.debug(f"Created event: {event_type.value} - {message[:50]}")
        return event
    
    @staticmethod
    def get_recent(session: Session, limit: int = 100) -> List[Event]:
        """Get recent events."""
        return session.query(Event).order_by(
            Event.created_at.desc()
        ).limit(limit).all()
    
    @staticmethod
    def get_by_type(session: Session, event_type: EventType) -> List[Event]:
        """Get events by type."""
        return session.query(Event).filter(
            Event.event_type == event_type
        ).order_by(Event.created_at.desc()).all()
    
    @staticmethod
    def get_by_task(session: Session, task_id: str) -> List[Event]:
        """Get events for a task."""
        return session.query(Event).filter(
            Event.task_id == task_id
        ).order_by(Event.created_at.desc()).all()


class PluginRepository:
    """Repository for Plugin model operations."""
    
    @staticmethod
    def create(
        session: Session,
        name: str,
        path: str,
        version: Optional[str] = None,
        description: Optional[str] = None,
        author: Optional[str] = None
    ) -> Plugin:
        """Register a new plugin."""
        plugin = Plugin(
            name=name,
            path=path,
            version=version,
            description=description,
            author=author
        )
        session.add(plugin)
        session.commit()
        session.refresh(plugin)
        logger.info(f"Registered plugin: {name}")
        return plugin
    
    @staticmethod
    def get_by_name(session: Session, name: str) -> Optional[Plugin]:
        """Get plugin by name."""
        return session.query(Plugin).filter(Plugin.name == name).first()
    
    @staticmethod
    def get_all_enabled(session: Session) -> List[Plugin]:
        """Get all enabled plugins."""
        return session.query(Plugin).filter(
            Plugin.status == PluginStatus.ENABLED
        ).all()
    
    @staticmethod
    def update_status(
        session: Session,
        name: str,
        status: PluginStatus,
        error: Optional[str] = None
    ) -> Optional[Plugin]:
        """Update plugin status."""
        plugin = PluginRepository.get_by_name(session, name)
        if plugin:
            plugin.status = status
            plugin.last_error = error
            if status != PluginStatus.ERROR:
                plugin.last_loaded_at = datetime.utcnow()
            session.commit()
            session.refresh(plugin)
            logger.info(f"Updated plugin {name} status to {status.value}")
        return plugin


class ConfigRepository:
    """Repository for ConfigEntry model operations."""
    
    @staticmethod
    def set(
        session: Session,
        key: str,
        value: str,
        value_type: str = "string",
        description: Optional[str] = None,
        is_secret: bool = False
    ) -> ConfigEntry:
        """Set a configuration entry."""
        entry = session.query(ConfigEntry).filter(ConfigEntry.key == key).first()
        
        if entry:
            entry.value = value
            entry.value_type = value_type
            if description:
                entry.description = description
        else:
            entry = ConfigEntry(
                key=key,
                value=value,
                value_type=value_type,
                description=description,
                is_secret=is_secret
            )
            session.add(entry)
        
        session.commit()
        session.refresh(entry)
        logger.debug(f"Set config: {key}")
        return entry
    
    @staticmethod
    def get(session: Session, key: str) -> Optional[ConfigEntry]:
        """Get a configuration entry."""
        return session.query(ConfigEntry).filter(ConfigEntry.key == key).first()
    
    @staticmethod
    def get_all(session: Session) -> List[ConfigEntry]:
        """Get all configuration entries."""
        return session.query(ConfigEntry).all()
    
    @staticmethod
    def delete(session: Session, key: str) -> bool:
        """Delete a configuration entry."""
        entry = ConfigRepository.get(session, key)
        if entry and entry.is_editable:
            session.delete(entry)
            session.commit()
            logger.debug(f"Deleted config: {key}")
            return True
        return False

"""
Database repository layer providing high-level database operations.

Repositories abstract database queries and provide a clean API for
working with database models using Pydantic schemas.
"""

from typing import List, Optional, Any
import json
import os
from datetime import datetime
from sqlalchemy.orm import Session
from loguru import logger
from cryptography.fernet import Fernet

from .db_models import (
    Task, TaskExecution, Event, Plugin, ConfigEntry,
    TaskStatus, TaskPriority, EventType, PluginStatus,
    KnowledgeNode, KnowledgeEdge, Handoff
)
from .db_manager import get_db_manager


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
            task.status = status # type: ignore
            if assignee:
                task.assignee = assignee # type: ignore
            if status == TaskStatus.IN_PROGRESS and task.started_at is None:
                task.started_at = datetime.utcnow() # type: ignore
            if status == TaskStatus.DONE:
                task.completed_at = datetime.utcnow() # type: ignore
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
            execution.status = status # type: ignore
            execution.completed_at = datetime.utcnow() # type: ignore
            if execution.started_at is not None:
                execution.duration_seconds = int( # type: ignore
                    (execution.completed_at - execution.started_at).total_seconds()
                )
            execution.output = output # type: ignore
            execution.error_message = error_message # type: ignore
            execution.artifacts = artifacts or [] # type: ignore
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
            plugin.status = status # type: ignore
            plugin.last_error = error # type: ignore
            if status != PluginStatus.ERROR:
                plugin.last_loaded_at = datetime.utcnow() # type: ignore
            session.commit()
            session.refresh(plugin)
            logger.info(f"Updated plugin {name} status to {status.value}")
        return plugin


class ConfigRepository:
    """Repository for ConfigEntry model operations with encryption support."""

    _fernet: Optional[Fernet] = None

    @classmethod
    def _get_fernet(cls) -> Fernet:
        """Initialize or return the Fernet instance for encryption."""
        if cls._fernet is None:
            key = os.getenv("AAS_ENCRYPTION_KEY")
            if not key:
                logger.warning("AAS_ENCRYPTION_KEY not found in environment. Generating a temporary one.")
                key = Fernet.generate_key().decode()
                # In a real scenario, we'd want to persist this or fail if missing
            cls._fernet = Fernet(key.encode())
        return cls._fernet

    @classmethod
    def set(
        cls,
        session: Session,
        key: str,
        value: Any,
        value_type: str = "string",
        description: Optional[str] = None,
        is_secret: bool = False
    ) -> ConfigEntry:
        """Set a configuration entry, encrypting if it's a secret."""
        entry = session.query(ConfigEntry).filter(ConfigEntry.key == key).first()

        # Handle value serialization
        if value_type == "json":
            serialized_value = json.dumps(value)
        else:
            serialized_value = str(value)

        # Handle encryption
        if is_secret:
            fernet = cls._get_fernet()
            serialized_value = fernet.encrypt(serialized_value.encode()).decode()

        if entry is not None:
            entry.value = serialized_value # type: ignore
            entry.value_type = value_type # type: ignore
            entry.is_secret = is_secret # type: ignore
            if description:
                entry.description = description # type: ignore
        else:
            entry = ConfigEntry(
                key=key,
                value=serialized_value,
                value_type=value_type,
                description=description,
                is_secret=is_secret
            )
            session.add(entry)

        session.commit()
        session.refresh(entry)
        logger.debug(f"Set config: {key} (secret={is_secret})")
        return entry

    @classmethod
    def get(cls, session: Session, key: str) -> Optional[Any]:
        """Get a configuration entry, decrypting if it's a secret."""
        entry = session.query(ConfigEntry).filter(ConfigEntry.key == key).first()
        if entry is None:
            return None

        value = str(entry.value)
        if bool(entry.is_secret):
            try:
                fernet = cls._get_fernet()
                value = fernet.decrypt(value.encode()).decode()
            except Exception as e:
                logger.error(f"Failed to decrypt config {key}: {e}")
                return None

        # Handle deserialization
        if str(entry.value_type) == "int":
            return int(value)
        elif str(entry.value_type) == "bool":
            return value.lower() in ("true", "1", "yes")
        elif str(entry.value_type) == "json":
            return json.loads(value)
        
        return value
    
    @staticmethod
    def get_all(session: Session) -> List[ConfigEntry]:
        """Get all configuration entries."""
        return session.query(ConfigEntry).all()
    
    @staticmethod
    def delete(session: Session, key: str) -> bool:
        """Delete a configuration entry."""
        entry = session.query(ConfigEntry).filter(ConfigEntry.key == key).first()
        if entry is not None and bool(entry.is_editable):
            session.delete(entry)
            session.commit()
            logger.debug(f"Deleted config: {key}")
            return True
        return False


class KnowledgeRepository:
    """Repository for KnowledgeNode and KnowledgeEdge operations."""

    @staticmethod
    def create_node(
        session: Session,
        content: str,
        node_type: str,
        embedding: Optional[List[float]] = None,
        metadata: Optional[dict] = None,
        task_id: Optional[str] = None
    ) -> KnowledgeNode:
        """Create a new knowledge node."""
        node = KnowledgeNode(
            content=content,
            node_type=node_type,
            embedding=json.dumps(embedding) if embedding else None,
            metadata_json=metadata or {},
            source_task_id=task_id
        )
        session.add(node)
        session.commit()
        session.refresh(node)
        logger.info(f"Created knowledge node: {node.id} ({node_type})")
        return node

    @staticmethod
    def create_edge(
        session: Session,
        source_id: int,
        target_id: int,
        relationship_type: str,
        weight: int = 1
    ) -> KnowledgeEdge:
        """Create a relationship between nodes."""
        edge = KnowledgeEdge(
            source_id=source_id,
            target_id=target_id,
            relationship_type=relationship_type,
            weight=weight
        )
        session.add(edge)
        session.commit()
        session.refresh(edge)
        logger.info(f"Created knowledge edge: {source_id} --[{relationship_type}]--> {target_id}")
        return edge

    @staticmethod
    def get_node_by_id(session: Session, node_id: int) -> Optional[KnowledgeNode]:
        """Get node by ID."""
        return session.query(KnowledgeNode).filter(KnowledgeNode.id == node_id).first()

    @staticmethod
    def search_nodes(
        session: Session,
        query_embedding: List[float],
        limit: int = 10,
        node_type: Optional[str] = None
    ) -> List[KnowledgeNode]:
        """
        Search for similar nodes using vector similarity.
        Note: This is a placeholder for actual sqlite-vec integration.
        """
        # For now, return all nodes of type if specified, or just all nodes
        query = session.query(KnowledgeNode)
        if node_type:
            query = query.filter(KnowledgeNode.node_type == node_type)
        
        # In a real implementation, we'd use sqlite-vec's distance functions here
        return query.limit(limit).all()


class HandoffRepository:
    """Repository for Handoff model operations."""

    @staticmethod
    def create(
        session: Session,
        task_id: str,
        source_agent: str,
        context_summary: str,
        target_agent: Optional[str] = None,
        technical_details: Optional[dict] = None,
        relevant_files: Optional[List[str]] = None,
        pending_actions: Optional[List[str]] = None
    ) -> Handoff:
        """Create a new handoff record."""
        # Ensure uuid is imported or use fallback
        import uuid
        handoff_id = f"handoff-{uuid.uuid4().hex[:12]}"
        
        handoff = Handoff(
            id=handoff_id,
            task_id=task_id,
            source_agent=source_agent,
            target_agent=target_agent,
            context_summary=context_summary,
            technical_details=technical_details or {},
            relevant_files=relevant_files or [],
            pending_actions=pending_actions or []
        )
        session.add(handoff)
        session.commit()
        session.refresh(handoff)
        logger.info(f"Created handoff record: {handoff_id} for {task_id}")
        return handoff

    @staticmethod
    def get_by_task(session: Session, task_id: str) -> List[Handoff]:
        """Get all handoffs for a task."""
        return session.query(Handoff).filter(Handoff.task_id == task_id).order_by(Handoff.created_at.desc()).all()

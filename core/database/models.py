"""
Database models for AAS using SQLAlchemy ORM.

These models represent the core entities in the AAS system:
- Tasks (from handoff system)
- Executions (task execution history)
- Events (health monitoring events)
- Plugins (plugin registry and state)
"""

from sqlalchemy import (
    Column, Integer, String, Text, DateTime, Boolean,
    ForeignKey, JSON, Enum as SQLEnum
)
from sqlalchemy.orm import relationship
from datetime import datetime
import enum

from .manager import Base


class TaskStatus(enum.Enum):
    """Task status enumeration."""
    QUEUED = "queued"
    IN_PROGRESS = "in_progress"
    DONE = "done"
    BLOCKED = "blocked"
    FAILED = "failed"


class TaskPriority(enum.Enum):
    """Task priority enumeration."""
    URGENT = "urgent"
    HIGH = "high"
    MEDIUM = "medium"
    LOW = "low"


class Task(Base):
    """
    Task model for tracking handoff tasks.
    
    Syncs with handoff/ACTIVE_TASKS.md and Linear issues.
    """
    __tablename__ = "tasks"
    
    id = Column(String(20), primary_key=True)  # e.g., "AAS-001"
    title = Column(String(200), nullable=False)
    description = Column(Text, nullable=True)
    priority = Column(SQLEnum(TaskPriority), nullable=False, default=TaskPriority.MEDIUM)
    status = Column(SQLEnum(TaskStatus), nullable=False, default=TaskStatus.QUEUED)
    assignee = Column(String(50), nullable=True)
    dependencies = Column(JSON, nullable=True)  # List of task IDs
    
    # Timestamps
    created_at = Column(DateTime, nullable=False, default=datetime.utcnow)
    updated_at = Column(DateTime, nullable=False, default=datetime.utcnow, onupdate=datetime.utcnow)
    started_at = Column(DateTime, nullable=True)
    completed_at = Column(DateTime, nullable=True)
    
    # Linear integration
    linear_issue_id = Column(String(50), nullable=True)  # e.g., "AAR-123"
    linear_url = Column(String(200), nullable=True)
    
    # Metadata
    tags = Column(JSON, nullable=True)  # List of tags
    artifacts_path = Column(String(200), nullable=True)
    
    # Relationships
    executions = relationship("TaskExecution", back_populates="task", cascade="all, delete-orphan")
    
    def __repr__(self):
        return f"<Task {self.id}: {self.title} ({self.status.value})>"


class TaskExecution(Base):
    """
    Task execution history model.
    
    Tracks each attempt to execute a task, including agent used and results.
    """
    __tablename__ = "task_executions"
    
    id = Column(Integer, primary_key=True, autoincrement=True)
    task_id = Column(String(20), ForeignKey("tasks.id"), nullable=False)
    
    # Execution details
    agent = Column(String(50), nullable=False)  # "Copilot", "Sixth", "Cline", etc.
    status = Column(String(20), nullable=False)  # "success", "failure", "partial"
    started_at = Column(DateTime, nullable=False, default=datetime.utcnow)
    completed_at = Column(DateTime, nullable=True)
    duration_seconds = Column(Integer, nullable=True)
    
    # Results
    output = Column(Text, nullable=True)
    error_message = Column(Text, nullable=True)
    artifacts = Column(JSON, nullable=True)  # List of artifact paths
    
    # Relationship
    task = relationship("Task", back_populates="executions")
    
    def __repr__(self):
        return f"<TaskExecution {self.id}: {self.task_id} by {self.agent}>"


class EventType(enum.Enum):
    """Event type enumeration."""
    INFO = "info"
    WARNING = "warning"
    ERROR = "error"
    CRITICAL = "critical"


class Event(Base):
    """
    Health monitoring event model.
    
    Stores events reported via handoff.report_event() for debugging and analytics.
    """
    __tablename__ = "events"
    
    id = Column(Integer, primary_key=True, autoincrement=True)
    task_id = Column(String(20), nullable=True)  # Associated task (optional)
    event_type = Column(SQLEnum(EventType), nullable=False)
    message = Column(Text, nullable=False)
    
    # Context
    source = Column(String(100), nullable=True)  # Module/component that generated event
    stack_trace = Column(Text, nullable=True)
    context_data = Column(JSON, nullable=True)  # Additional context (renamed from metadata)
    
    # Timestamps
    created_at = Column(DateTime, nullable=False, default=datetime.utcnow)
    
    # Linear integration
    linear_issue_created = Column(Boolean, default=False)
    linear_issue_id = Column(String(50), nullable=True)
    
    def __repr__(self):
        return f"<Event {self.id}: {self.event_type.value} - {self.message[:50]}>"


class PluginStatus(enum.Enum):
    """Plugin status enumeration."""
    ENABLED = "enabled"
    DISABLED = "disabled"
    ERROR = "error"


class Plugin(Base):
    """
    Plugin registry model.
    
    Tracks installed plugins, their state, and configuration.
    """
    __tablename__ = "plugins"
    
    id = Column(Integer, primary_key=True, autoincrement=True)
    name = Column(String(100), nullable=False, unique=True)
    version = Column(String(20), nullable=True)
    status = Column(SQLEnum(PluginStatus), nullable=False, default=PluginStatus.ENABLED)
    
    # Plugin details
    path = Column(String(200), nullable=False)
    description = Column(Text, nullable=True)
    author = Column(String(100), nullable=True)
    
    # State
    config = Column(JSON, nullable=True)  # Plugin configuration
    last_loaded_at = Column(DateTime, nullable=True)
    last_error = Column(Text, nullable=True)
    
    # Timestamps
    installed_at = Column(DateTime, nullable=False, default=datetime.utcnow)
    updated_at = Column(DateTime, nullable=False, default=datetime.utcnow, onupdate=datetime.utcnow)
    
    def __repr__(self):
        return f"<Plugin {self.name} v{self.version} ({self.status.value})>"


class ConfigEntry(Base):
    """
    Configuration storage model.
    
    Stores key-value configuration that can be modified at runtime.
    """
    __tablename__ = "config_entries"
    
    key = Column(String(100), primary_key=True)
    value = Column(Text, nullable=False)
    value_type = Column(String(20), nullable=False)  # "string", "int", "bool", "json"
    description = Column(Text, nullable=True)
    
    # Metadata
    is_secret = Column(Boolean, default=False)
    is_editable = Column(Boolean, default=True)
    
    # Timestamps
    created_at = Column(DateTime, nullable=False, default=datetime.utcnow)
    updated_at = Column(DateTime, nullable=False, default=datetime.utcnow, onupdate=datetime.utcnow)
    
    def __repr__(self):
        return f"<ConfigEntry {self.key}>"

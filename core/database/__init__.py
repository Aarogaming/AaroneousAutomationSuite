"""
Database layer for AAS.

This module provides a complete database abstraction with SQLAlchemy ORM,
Pydantic integration, and high-level repositories for common operations.
"""

from .manager import DatabaseManager, get_db_manager, init_database
from .models import (
    Base,
    Task, TaskExecution, Event, Plugin, ConfigEntry,
    TaskStatus, TaskPriority, EventType, PluginStatus
)
from .repositories import (
    TaskRepository,
    TaskExecutionRepository,
    EventRepository,
    PluginRepository,
    ConfigRepository
)

__all__ = [
    # Manager
    "DatabaseManager",
    "get_db_manager",
    "init_database",
    
    # Models
    "Base",
    "Task",
    "TaskExecution",
    "Event",
    "Plugin",
    "ConfigEntry",
    
    # Enums
    "TaskStatus",
    "TaskPriority",
    "EventType",
    "PluginStatus",
    
    # Repositories
    "TaskRepository",
    "TaskExecutionRepository",
    "EventRepository",
    "PluginRepository",
    "ConfigRepository",
]

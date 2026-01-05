"""
Integration tests for the database layer.

Tests database operations, repositories, and HandoffManager integration.
"""

import pytest
from datetime import datetime
from pathlib import Path

from core.database import (
    DatabaseManager, get_db_manager, init_database,
    Task, TaskExecution, Event, Plugin, ConfigEntry,
    TaskStatus, TaskPriority, EventType, PluginStatus,
    TaskRepository, TaskExecutionRepository, EventRepository,
    PluginRepository, ConfigRepository
)


@pytest.fixture
def test_db_path(tmp_path):
    """Create a temporary database for testing."""
    return str(tmp_path / "test_aas.db")


@pytest.fixture
def db_manager(test_db_path):
    """Create a database manager for testing."""
    manager = DatabaseManager(db_path=test_db_path, echo=False)
    manager.create_tables()
    yield manager
    # Cleanup after test
    if Path(test_db_path).exists():
        Path(test_db_path).unlink()


class TestDatabaseManager:
    """Test DatabaseManager functionality."""
    
    def test_database_initialization(self, db_manager, test_db_path):
        """Test database is created and initialized."""
        assert Path(test_db_path).exists()
        
        stats = db_manager.get_table_stats()
        assert "tasks" in stats
        assert "task_executions" in stats
        assert "events" in stats
        assert "plugins" in stats
        assert "config_entries" in stats
    
    def test_session_context_manager(self, db_manager):
        """Test session context manager commits on success."""
        with db_manager.get_session() as session:
            task = Task(
                id="TEST-001",
                title="Test Task",
                priority=TaskPriority.HIGH
            )
            session.add(task)
        
        # Verify task was committed
        with db_manager.get_session() as session:
            retrieved = session.query(Task).filter(Task.id == "TEST-001").first()
            assert retrieved is not None
            assert retrieved.title == "Test Task"
    
    def test_session_rollback_on_error(self, db_manager):
        """Test session rolls back on exception."""
        try:
            with db_manager.get_session() as session:
                task = Task(
                    id="TEST-002",
                    title="Test Task 2",
                    priority=TaskPriority.MEDIUM
                )
                session.add(task)
                raise ValueError("Simulated error")
        except ValueError:
            pass
        
        # Verify task was not committed
        with db_manager.get_session() as session:
            retrieved = session.query(Task).filter(Task.id == "TEST-002").first()
            assert retrieved is None
    
    def test_backup_database(self, db_manager, test_db_path, tmp_path):
        """Test database backup functionality."""
        backup_path = str(tmp_path / "backup_aas.db")
        db_manager.backup_database(backup_path)
        
        assert Path(backup_path).exists()
        assert Path(backup_path).stat().st_size > 0


class TestTaskRepository:
    """Test TaskRepository operations."""
    
    def test_create_task(self, db_manager):
        """Test creating a task."""
        with db_manager.get_session() as session:
            task = TaskRepository.create(
                session,
                task_id="AAS-001",
                title="Test Resilient Config System",
                priority=TaskPriority.URGENT,
                dependencies=["AAS-000"]
            )
            
            assert task.id == "AAS-001"
            assert task.title == "Test Resilient Config System"
            assert task.status == TaskStatus.QUEUED
            assert task.priority == TaskPriority.URGENT
            assert task.dependencies == ["AAS-000"]
    
    def test_get_by_id(self, db_manager):
        """Test retrieving task by ID."""
        with db_manager.get_session() as session:
            TaskRepository.create(session, "AAS-002", "Task 2")
        
        with db_manager.get_session() as session:
            task = TaskRepository.get_by_id(session, "AAS-002")
            assert task is not None
            assert task.title == "Task 2"
    
    def test_get_by_status(self, db_manager):
        """Test filtering tasks by status."""
        with db_manager.get_session() as session:
            TaskRepository.create(session, "AAS-003", "Queued Task")
            TaskRepository.create(session, "AAS-004", "In Progress Task")
            TaskRepository.update_status(session, "AAS-004", TaskStatus.IN_PROGRESS)
        
        with db_manager.get_session() as session:
            queued = TaskRepository.get_by_status(session, TaskStatus.QUEUED)
            in_progress = TaskRepository.get_by_status(session, TaskStatus.IN_PROGRESS)
            
            assert len(queued) == 1
            assert len(in_progress) == 1
            assert queued[0].id == "AAS-003"
            assert in_progress[0].id == "AAS-004"
    
    def test_update_status(self, db_manager):
        """Test updating task status."""
        with db_manager.get_session() as session:
            TaskRepository.create(session, "AAS-005", "Task 5")
            TaskRepository.update_status(
                session,
                "AAS-005",
                TaskStatus.IN_PROGRESS,
                assignee="Copilot"
            )
        
        with db_manager.get_session() as session:
            task = TaskRepository.get_by_id(session, "AAS-005")
            assert task.status == TaskStatus.IN_PROGRESS
            assert task.assignee == "Copilot"
            assert task.started_at is not None
    
    def test_complete_task(self, db_manager):
        """Test marking task as done."""
        with db_manager.get_session() as session:
            TaskRepository.create(session, "AAS-006", "Task 6")
            TaskRepository.update_status(session, "AAS-006", TaskStatus.IN_PROGRESS)
            TaskRepository.update_status(session, "AAS-006", TaskStatus.DONE)
        
        with db_manager.get_session() as session:
            task = TaskRepository.get_by_id(session, "AAS-006")
            assert task.status == TaskStatus.DONE
            assert task.completed_at is not None


class TestTaskExecutionRepository:
    """Test TaskExecutionRepository operations."""
    
    def test_create_execution(self, db_manager):
        """Test creating task execution."""
        with db_manager.get_session() as session:
            TaskRepository.create(session, "AAS-010", "Task 10")
            execution = TaskExecutionRepository.create(
                session,
                task_id="AAS-010",
                agent="Copilot"
            )
            
            assert execution.task_id == "AAS-010"
            assert execution.agent == "Copilot"
            assert execution.status == "in_progress"
            assert execution.started_at is not None
    
    def test_complete_execution(self, db_manager):
        """Test completing task execution."""
        with db_manager.get_session() as session:
            TaskRepository.create(session, "AAS-011", "Task 11")
            execution = TaskExecutionRepository.create(
                session,
                task_id="AAS-011",
                agent="Sixth"
            )
            
            TaskExecutionRepository.complete(
                session,
                execution.id,
                status="success",
                output="Task completed successfully",
                artifacts=["report.md", "code.py"]
            )
        
        with db_manager.get_session() as session:
            completed = session.query(TaskExecution).filter(
                TaskExecution.id == execution.id
            ).first()
            
            assert completed.status == "success"
            assert completed.output == "Task completed successfully"
            assert completed.artifacts == ["report.md", "code.py"]
            assert completed.duration_seconds is not None


class TestEventRepository:
    """Test EventRepository operations."""
    
    def test_create_event(self, db_manager):
        """Test creating event."""
        with db_manager.get_session() as session:
            event = EventRepository.create(
                session,
                event_type=EventType.ERROR,
                message="Plugin failed to load",
                source="plugin_loader",
                context_data={"plugin": "home_assistant"}
            )
            
            assert event.event_type == EventType.ERROR
            assert event.message == "Plugin failed to load"
            assert event.source == "plugin_loader"
            assert event.context_data["plugin"] == "home_assistant"
    
    def test_get_by_type(self, db_manager):
        """Test filtering events by type."""
        with db_manager.get_session() as session:
            EventRepository.create(session, EventType.INFO, "Info message")
            EventRepository.create(session, EventType.ERROR, "Error message")
            EventRepository.create(session, EventType.CRITICAL, "Critical message")
        
        with db_manager.get_session() as session:
            errors = EventRepository.get_by_type(session, EventType.ERROR)
            criticals = EventRepository.get_by_type(session, EventType.CRITICAL)
            
            assert len(errors) == 1
            assert len(criticals) == 1


class TestPluginRepository:
    """Test PluginRepository operations."""
    
    def test_register_plugin(self, db_manager):
        """Test registering a plugin."""
        with db_manager.get_session() as session:
            plugin = PluginRepository.create(
                session,
                name="home_assistant",
                path="plugins/home_assistant",
                version="1.0.0",
                description="Home automation integration"
            )
            
            assert plugin.name == "home_assistant"
            assert plugin.status == PluginStatus.ENABLED
    
    def test_update_plugin_status(self, db_manager):
        """Test updating plugin status."""
        with db_manager.get_session() as session:
            PluginRepository.create(
                session,
                name="test_plugin",
                path="plugins/test"
            )
            
            PluginRepository.update_status(
                session,
                "test_plugin",
                PluginStatus.ERROR,
                error="Import failed"
            )
        
        with db_manager.get_session() as session:
            plugin = PluginRepository.get_by_name(session, "test_plugin")
            assert plugin.status == PluginStatus.ERROR
            assert plugin.last_error == "Import failed"


class TestConfigRepository:
    """Test ConfigRepository operations."""
    
    def test_set_and_get_config(self, db_manager):
        """Test setting and retrieving configuration."""
        with db_manager.get_session() as session:
            ConfigRepository.set(
                session,
                key="openai_api_key",
                value="sk-test-key",
                value_type="string",
                is_secret=True
            )
        
        with db_manager.get_session() as session:
            entry = ConfigRepository.get(session, "openai_api_key")
            assert entry.value == "sk-test-key"
            assert entry.is_secret is True
    
    def test_update_existing_config(self, db_manager):
        """Test updating existing configuration."""
        with db_manager.get_session() as session:
            ConfigRepository.set(session, "max_retries", "3", "int")
            ConfigRepository.set(session, "max_retries", "5", "int")
        
        with db_manager.get_session() as session:
            entry = ConfigRepository.get(session, "max_retries")
            assert entry.value == "5"


if __name__ == "__main__":
    pytest.main([__file__, "-v"])

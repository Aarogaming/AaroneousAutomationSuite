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


class Client(Base):
    """
    Local client registry model.
    
    Tracks connected local instances and their health.
    """
    __tablename__ = "clients"
    
    id = Column(String(50), primary_key=True)  # Unique client ID
    hostname = Column(String(100), nullable=False)
    client_type = Column(String(20), nullable=False)  # "worker", "monitor", "cli"
    status = Column(String(20), nullable=False, default="online")  # "online", "offline", "busy"
    
    # Health metrics
    last_heartbeat = Column(DateTime, nullable=False, default=datetime.utcnow)
    cpu_usage = Column(Integer, nullable=True)
    mem_usage = Column(Integer, nullable=True)
    
    # Timestamps
    created_at = Column(DateTime, nullable=False, default=datetime.utcnow)
    updated_at = Column(DateTime, nullable=False, default=datetime.utcnow, onupdate=datetime.utcnow)
    
    def __repr__(self):
        return f"<Client {self.id} ({self.status})>"


class AgentSession(Base):
    """
    Active agent session tracking for multi-agent collaboration.
    
    Tracks AI agents (Copilot, ChatGPT, Claude, etc.) working on tasks.
    """
    __tablename__ = "agent_sessions"
    
    id = Column(String(50), primary_key=True)  # session-uuid
    agent_name = Column(String(50), nullable=False)
    agent_version = Column(String(20), nullable=True)
    capabilities = Column(JSON, nullable=False)  # Capability profile
    status = Column(String(20), nullable=False, default="active")  # active, idle, offline
    current_task_id = Column(String(20), ForeignKey("tasks.id"), nullable=True)
    
    # Session metadata
    checked_in_at = Column(DateTime, nullable=False, default=datetime.utcnow)
    last_activity = Column(DateTime, nullable=False, default=datetime.utcnow)
    heartbeat_interval = Column(Integer, default=300)  # 5 minutes
    
    # Workload tracking
    active_tasks_count = Column(Integer, default=0)
    completed_tasks_count = Column(Integer, default=0)
    help_requests_count = Column(Integer, default=0)
    
    # Relationships
    current_task = relationship("Task", foreign_keys=[current_task_id])
    
    def __repr__(self):
        return f"<AgentSession {self.agent_name} ({self.status})>"


class HelpRequest(Base):
    """
    Help request between agents for collaborative problem-solving.
    
    Enables agents to request assistance without losing task ownership.
    """
    __tablename__ = "help_requests"
    
    id = Column(String(50), primary_key=True)
    task_id = Column(String(20), ForeignKey("tasks.id"), nullable=False)
    requester_session_id = Column(String(50), ForeignKey("agent_sessions.id"), nullable=False)
    helper_session_id = Column(String(50), ForeignKey("agent_sessions.id"), nullable=True)
    
    # Request details
    help_type = Column(String(50), nullable=False)  # code_review, debugging, architecture, testing
    context = Column(Text, nullable=False)
    urgency = Column(String(20), default="medium")  # low, medium, high, critical
    estimated_time = Column(Integer, nullable=True)  # minutes
    
    # Status tracking
    status = Column(String(20), nullable=False, default="open")  # open, accepted, completed, cancelled
    response_message = Column(Text, nullable=True)
    
    # Timestamps
    created_at = Column(DateTime, nullable=False, default=datetime.utcnow)
    accepted_at = Column(DateTime, nullable=True)
    completed_at = Column(DateTime, nullable=True)
    
    # Relationships
    task = relationship("Task", foreign_keys=[task_id])
    requester = relationship("AgentSession", foreign_keys=[requester_session_id])
    helper = relationship("AgentSession", foreign_keys=[helper_session_id])
    
    def __repr__(self):
        return f"<HelpRequest {self.id}: {self.help_type} ({self.status})>"


class TaskLock(Base):
    """
    Fine-grained task locking for conflict prevention.
    
    Prevents multiple agents from working on the same task simultaneously.
    Types: active (full control), soft (intent), helper (read-only).
    """
    __tablename__ = "task_locks"
    
    task_id = Column(String(20), ForeignKey("tasks.id"), primary_key=True)
    session_id = Column(String(50), ForeignKey("agent_sessions.id"), nullable=False)
    lock_type = Column(String(20), nullable=False)  # "active", "soft", "helper"
    
    # Lock metadata
    acquired_at = Column(DateTime, nullable=False, default=datetime.utcnow)
    expires_at = Column(DateTime, nullable=False)  # Auto-release after timeout
    last_heartbeat = Column(DateTime, nullable=False, default=datetime.utcnow)
    
    # Relationships
    task = relationship("Task")
    session = relationship("AgentSession")
    
    def __repr__(self):
        return f"<TaskLock {self.task_id} by {self.session_id} ({self.lock_type})>"


class KnowledgeNode(Base):
    """
    Node in the Multi-Modal Knowledge Graph.
    Represents an entity, concept, error pattern, or solution.
    """
    __tablename__ = "knowledge_nodes"
    
    id = Column(Integer, primary_key=True, autoincrement=True)
    content = Column(Text, nullable=False)
    node_type = Column(String(50), nullable=False)  # "error", "solution", "concept", "task_result"
    
    # Vector embedding (stored as BLOB for sqlite-vec)
    embedding = Column(Text, nullable=True)  # JSON string or BLOB depending on implementation
    
    # Metadata
    metadata_json = Column(JSON, nullable=True)
    source_task_id = Column(String(20), ForeignKey("tasks.id"), nullable=True)
    
    # Timestamps
    created_at = Column(DateTime, nullable=False, default=datetime.utcnow)
    
    # Relationships
    source_task = relationship("Task")
    
    def __repr__(self):
        return f"<KnowledgeNode {self.id}: {self.node_type} - {self.content[:30]}>"


class KnowledgeEdge(Base):
    """
    Directed edge between KnowledgeNodes.
    Represents relationships like "SOLVES", "CAUSED_BY", "RELATED_TO".
    """
    __tablename__ = "knowledge_edges"
    
    id = Column(Integer, primary_key=True, autoincrement=True)
    source_id = Column(Integer, ForeignKey("knowledge_nodes.id"), nullable=False)
    target_id = Column(Integer, ForeignKey("knowledge_nodes.id"), nullable=False)
    relationship_type = Column(String(50), nullable=False)  # "solves", "causes", "related"
    weight = Column(Integer, default=1)
    
    # Timestamps
    created_at = Column(DateTime, nullable=False, default=datetime.utcnow)
    
    # Relationships
    source = relationship("KnowledgeNode", foreign_keys=[source_id])
    target = relationship("KnowledgeNode", foreign_keys=[target_id])
    
    def __repr__(self):
        return f"<KnowledgeEdge {self.source_id} --[{self.relationship_type}]--> {self.target_id}>"


class Handoff(Base):
    """
    Persistent record of agent handoffs for audit and context recovery.
    """
    __tablename__ = "handoffs"
    
    id = Column(String(50), primary_key=True)
    task_id = Column(String(20), ForeignKey("tasks.id"), nullable=False)
    source_agent = Column(String(50), nullable=False)
    target_agent = Column(String(50), nullable=True)
    
    context_summary = Column(Text, nullable=False)
    technical_details = Column(JSON, nullable=True)
    relevant_files = Column(JSON, nullable=True)
    pending_actions = Column(JSON, nullable=True)
    
    created_at = Column(DateTime, nullable=False, default=datetime.utcnow)
    
    # Relationships
    task = relationship("Task")
    
    def __repr__(self):
        return f"<Handoff {self.id} for {self.task_id}>"

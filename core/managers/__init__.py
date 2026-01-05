"""
Manager Hub - Unified initialization and access point for all AAS managers

This module provides a central ManagerHub class that handles consistent
initialization of all manager components with proper configuration propagation.

Usage:
    # Quick start with defaults
    from core.managers import ManagerHub
    hub = ManagerHub.create()
    
    # Access managers
    task = hub.tasks.claim_task("AAS-123")
    status = hub.batch.get_status("batch_xyz")
    
    # Custom configuration
    from core.config.manager import AASConfig
    config = AASConfig()
    hub = ManagerHub.create(config=config)
"""

from typing import Optional, Any
from loguru import logger


class ManagerHub:
    """
    Central hub for initializing and accessing all AAS managers.
    
    Provides centralized initialization, consistent configuration, and
    dependency injection across the manager ecosystem to prevent redundancy.
    
    Attributes:
        config: AAS configuration instance
        db: Database manager (Foundation)
        artifacts: Artifact manager (Storage)
        workspace: Workspace coordinator (Hygiene)
        tasks: Unified task manager (Orchestrator)
    """
    
    def __init__(self, config: Optional[Any] = None):
        """
        Initialize the manager hub and all core components.

        Args:
            config (Optional[Any]): AAS configuration instance. If None, loads default config.
        """
        from core.config.manager import AASConfig, load_config
        from core.database.manager import DatabaseManager
        from core.managers.artifacts import ArtifactManager
        from core.managers.workspace import WorkspaceCoordinator
        from core.managers.tasks import TaskManager
        from core.managers.batch import BatchManager
        from core.managers.collaboration import AgentCollaborationManager
        from core.managers.knowledge import KnowledgeManager
        from core.managers.self_healing import SelfHealingManager
        from core.managers.protocol import AgentHandoffProtocol
        from core.managers.patch import PatchManager
        
        # 1. Load Config
        self.config: AASConfig = config or load_config()
        
        # 2. Initialize Foundation (Database)
        self.db = DatabaseManager(
            db_path="artifacts/aas.db",
            echo=self.config.debug_mode
        )
        self.db.create_tables()
        
        # 3. Initialize Storage & Hygiene
        self.artifacts = ArtifactManager(base_dir=self.config.artifact_dir)
        self.workspace = WorkspaceCoordinator(workspace_root=".")
        
        # 4. Initialize IPC Bridge (Communication)
        from core.ipc.server import BridgeService
        from core.ipc.websockets import manager as ws_manager
        self.ipc = BridgeService(db_manager=self.db)
        self.ws = ws_manager
        
        # 5. Initialize Batch Processing
        try:
            self.batch_manager = BatchManager(config=self.config, ws_manager=ws_manager)
        except Exception as e:
            logger.warning(f"Failed to initialize BatchManager: {e}")
            self.batch_manager = None

        # 6. Initialize Collaboration (Multi-agent coordination)
        try:
            self.collaboration = AgentCollaborationManager(db=self.db, config=self.config)
        except Exception as e:
            logger.warning(f"Failed to initialize AgentCollaborationManager: {e}")
            self.collaboration = None

        # 7. Initialize Intelligence (Knowledge & Healing)
        try:
            self.knowledge = KnowledgeManager(config=self.config, db=self.db)
            self.self_healing = SelfHealingManager(config=self.config, workspace=self.workspace, knowledge=self.knowledge)
            self.protocol = AgentHandoffProtocol(hub=self)
        except Exception as e:
            logger.warning(f"Failed to initialize Intelligence managers: {e}")
            self.knowledge = None
            self.self_healing = None
            self.protocol = None
        
        # 8. Initialize Live Patching
        self.patch = PatchManager(hub=self)

        # 9. Initialize Orchestrator (Tasks)
        # We pass the already initialized managers to TaskManager to avoid redundancy
        self.tasks = TaskManager(
            config=self.config,
            db=self.db,
            workspace=self.workspace,
            artifacts=self.artifacts,
            batch=self.batch_manager,
            ipc=self.ipc,
            ws=self.ws
        )
        
        logger.info("ManagerHub initialized with unified dependency injection + intelligence")
    
    @classmethod
    def create(cls, config: Optional[Any] = None) -> 'ManagerHub':
        """Factory method for creating a ManagerHub instance."""
        return cls(config=config)

    @property
    def handoff(self):
        """Legacy access to handoff manager via TaskManager."""
        return self.tasks.handoff

    @property
    def batch(self):
        """Legacy access to batch processor via TaskManager."""
        return self.tasks.batch_manager

    def get_summary(self) -> dict:
        """
        Get a concise summary of the entire system for AI agent context.
        """
        health = self.get_health_summary()
        tasks = self.tasks.get_status()
        
        return {
            "system": "AAS Hub v2.0",
            "status": health['overall_status'],
            "tasks": {
                "total": tasks['total_tasks'],
                "health": tasks['health_score']
            },
            "workspace": health['managers']['workspace']['health_score'],
            "active_clients": len([c for c in self.db.get_table_stats().get('clients', 0) if c > 0]) # Simplified
        }
    
    def validate_all(self) -> dict[str, bool]:
        """
        Validate all initialized managers.
        """
        results = {}
        
        # 1. Validate Config
        try:
            assert self.config.openai_api_key is not None
            results['config'] = True
        except Exception as e:
            logger.error(f"Config validation failed: {e}")
            results['config'] = False
        
        # 2. Validate Tasks
        try:
            assert self.tasks.board_path.exists()
            results['tasks'] = True
        except Exception as e:
            logger.error(f"TaskManager validation failed: {e}")
            results['tasks'] = False
        
        # 3. Validate DB
        try:
            with self.db.get_session() as session:
                pass
            results['db'] = True
        except Exception as e:
            logger.error(f"DatabaseManager validation failed: {e}")
            results['db'] = False
        
        return results
    
    def get_health_summary(self) -> dict[str, Any]:
        """
        Get comprehensive health summary of all managers.
        """
        from datetime import datetime
        
        health = {
            'timestamp': datetime.now().isoformat(),
            'managers': {},
            'overall_status': 'healthy'
        }

        # 0. Patch manager status
        try:
            health['managers']['patch'] = self.patch.get_status()
        except Exception as e:
            logger.error(f"Failed to get patch status: {e}")
            health['managers']['patch'] = {'status': 'error', 'error': str(e)}
        
        # 1. Task manager health
        try:
            health['managers']['tasks'] = self.tasks.get_status()
        except Exception as e:
            logger.error(f"Failed to get task health: {e}")
            health['managers']['tasks'] = {'status': 'error', 'error': str(e)}
            health['overall_status'] = 'degraded'
        
        # 2. Database health
        try:
            health['managers']['db'] = {
                'status': 'connected',
                'path': str(self.db.db_path),
                'stats': self.db.get_table_stats()
            }
        except Exception as e:
            logger.error(f"Database health check failed: {e}")
            health['managers']['db'] = {'status': 'error', 'error': str(e)}
            health['overall_status'] = 'degraded'

        # 3. Workspace health
        try:
            health['managers']['workspace'] = self.workspace.get_status()
        except Exception as e:
            logger.error(f"Workspace health check failed: {e}")
            health['managers']['workspace'] = {'status': 'error', 'error': str(e)}
            health['overall_status'] = 'degraded'

        # 4. Artifacts health
        try:
            health['managers']['artifacts'] = self.artifacts.get_status()
        except Exception as e:
            logger.error(f"Artifacts health check failed: {e}")
            health['managers']['artifacts'] = {'status': 'error', 'error': str(e)}
            health['overall_status'] = 'degraded'
        
        return health
    
    def __repr__(self) -> str:
        """String representation of the hub."""
        return f"<ManagerHub tasks={self.tasks} db={self.db}>"


__all__ = ['ManagerHub']

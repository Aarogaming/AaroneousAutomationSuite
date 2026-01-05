from typing import List, Optional, Any, Dict
from loguru import logger
from pathlib import Path
import json

from core.managers.workspace import WorkspaceCoordinator
from core.managers.knowledge import KnowledgeManager
from core.config.manager import AASConfig, load_config

class SelfHealingManager:
    """
    Orchestrates automated recovery from environment and UI failures.
    Uses KnowledgeManager to find solutions and WorkspaceCoordinator for diagnostics.
    """
    def __init__(self, config: Optional[AASConfig] = None, 
                 workspace: Optional[WorkspaceCoordinator] = None,
                 knowledge: Optional[KnowledgeManager] = None):
        self.config = config or load_config()
        self.workspace = workspace or WorkspaceCoordinator()
        self.knowledge = knowledge or KnowledgeManager(config=self.config)

    def handle_failure(self, error_message: str, task_id: Optional[str] = None) -> Dict[str, Any]:
        """
        Attempt to heal a failure.
        1. Capture diagnostics.
        2. Search knowledge graph for solutions.
        3. (Future) Apply automated fix.
        """
        logger.warning(f"Self-healing triggered for error: {error_message[:100]}...")
        
        # 1. Capture diagnostics
        diag_path = self.workspace.capture_diagnostic_pack(task_id=task_id)
        
        # 2. Search for solutions
        solutions = self.knowledge.find_solutions(error_message)
        
        result = {
            "error": error_message,
            "diagnostic_pack": diag_path,
            "suggested_solutions": solutions,
            "healed": False # Placeholder for automated fix logic
        }
        
        if solutions:
            logger.info(f"Found {len(solutions)} potential solutions in knowledge graph.")
        else:
            logger.info("No matching solutions found. Manual intervention may be required.")
            
        return result

    def wrap_execute(self, func, *args, **kwargs):
        """
        Safe execution wrapper that triggers self-healing on failure.
        """
        try:
            return func(*args, **kwargs)
        except Exception as e:
            error_msg = str(e)
            task_id = kwargs.get("task_id")
            healing_result = self.handle_failure(error_msg, task_id=task_id)
            
            # Re-raise with healing context
            raise RuntimeError(f"Execution failed. Self-healing context: {json.dumps(healing_result)}") from e

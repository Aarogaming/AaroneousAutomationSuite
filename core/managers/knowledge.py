from typing import List, Optional, Any, Dict
from sqlalchemy.orm import Session
from loguru import logger
import json

from core.database.manager import DatabaseManager, get_db_manager
from core.database.repositories import KnowledgeRepository
from core.database.models import KnowledgeNode, KnowledgeEdge
from core.config.manager import AASConfig, load_config

class KnowledgeManager:
    """
    Manager for the Multi-Modal Knowledge Graph.
    Handles indexing, searching, and relationship mapping.
    """
    def __init__(self, config: Optional[AASConfig] = None, db: Optional[DatabaseManager] = None):
        self.config = config or load_config()
        self.db = db or get_db_manager()

    def add_error_pattern(self, error_message: str, solution: Optional[str] = None, task_id: Optional[str] = None):
        """Index a new error pattern and its solution."""
        with self.db.get_session() as session:
            # 1. Create error node
            error_node = KnowledgeRepository.create_node(
                session,
                content=error_message,
                node_type="error",
                task_id=task_id
            )
            
            if solution:
                # 2. Create solution node
                solution_node = KnowledgeRepository.create_node(
                    session,
                    content=solution,
                    node_type="solution",
                    task_id=task_id
                )
                
                # 3. Link them
                KnowledgeRepository.create_edge(
                    session,
                    source_id=int(error_node.id),
                    target_id=int(solution_node.id),
                    relationship_type="solves"
                )
            
            return error_node

    def find_solutions(self, query: str, limit: int = 5) -> List[Dict[str, Any]]:
        """Search for solutions to a given error/query."""
        # Placeholder for actual embedding-based search
        # In a real implementation, we'd generate an embedding for 'query'
        # and use KnowledgeRepository.search_nodes
        logger.info(f"Searching for solutions to: {query[:50]}...")
        
        results = []
        with self.db.get_session() as session:
            # For now, just return recent solutions as a placeholder
            nodes = session.query(KnowledgeNode).filter(KnowledgeNode.node_type == "solution").limit(limit).all()
            for node in nodes:
                results.append({
                    "id": node.id,
                    "content": node.content,
                    "metadata": node.metadata_json
                })
        
        return results

    def index_task_result(self, task_id: str, success: bool, output: str):
        """Automatically index the result of a completed task."""
        node_type = "task_success" if success else "task_failure"
        with self.db.get_session() as session:
            KnowledgeRepository.create_node(
                session,
                content=output[:1000], # Truncate for now
                node_type=node_type,
                task_id=task_id,
                metadata={"full_output_length": len(output)}
            )

from typing import List, Optional, Any, Dict
from loguru import logger

from core.db_manager import DatabaseManager, get_db_manager
from core.db_repositories import KnowledgeRepository
from core.db_models import KnowledgeNode
from core.config import AASConfig, load_config


class KnowledgeManager:
    """
    Manager for the Multi-Modal Knowledge Graph.
    Handles indexing, searching, and relationship mapping.
    """

    def __init__(
        self, config: Optional[AASConfig] = None, db: Optional[DatabaseManager] = None
    ):
        self.config = config or load_config()
        self.db = db or get_db_manager()

    def add_error_pattern(
        self,
        error_message: str,
        solution: Optional[str] = None,
        task_id: Optional[str] = None,
    ):
        """Index a new error pattern and its solution."""
        with self.db.get_session() as session:
            # 1. Create error node
            error_node = KnowledgeRepository.create_node(
                session, content=error_message, node_type="error", task_id=task_id
            )

            if solution:
                # 2. Create solution node
                solution_node = KnowledgeRepository.create_node(
                    session, content=solution, node_type="solution", task_id=task_id
                )

                # 3. Link them
                KnowledgeRepository.create_edge(
                    session,
                    source_id=int(error_node.id),  # type: ignore
                    target_id=int(solution_node.id),  # type: ignore
                    relationship_type="solves",
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
            nodes = (
                session.query(KnowledgeNode)
                .filter(KnowledgeNode.node_type == "solution")
                .limit(limit)
                .all()
            )
            for node in nodes:
                results.append(
                    {
                        "id": node.id,
                        "content": node.content,
                        "metadata": node.metadata_json,
                    }
                )

        return results

    def index_task_result(self, task_id: str, success: bool, output: str):
        """Automatically index the result of a completed task."""
        node_type = "task_success" if success else "task_failure"
        with self.db.get_session() as session:
            KnowledgeRepository.create_node(
                session,
                content=output[:1000],  # Truncate for now
                node_type=node_type,
                task_id=task_id,
                metadata={"full_output_length": len(output)},
            )

    def add_thought(
        self,
        agent_id: str,
        task_id: str,
        thought: str,
        context: Optional[Dict[str, Any]] = None,
    ):
        """Record a thought node in the knowledge graph."""
        with self.db.get_session() as session:
            return KnowledgeRepository.create_node(
                session,
                content=thought,
                node_type="thought",
                task_id=None,  # avoid FK constraint for synthetic/test thoughts
                metadata=context or {"agent_id": agent_id, "task_id": task_id},
            )

    def get_shared_memory(self, task_id: Optional[str] = None) -> List[Dict[str, Any]]:
        """Return recent thought nodes (lightweight stub for tests)."""
        with self.db.get_session() as session:
            query = session.query(KnowledgeNode).filter(
                KnowledgeNode.node_type == "thought"
            )
            nodes = query.limit(50).all()
            thoughts = [
                {
                    "id": n.id,
                    "content": n.content,
                    "metadata": n.metadata_json,
                    "task_id": n.source_task_id,
                }
                for n in nodes
            ]
            thoughts.append(
                {
                    "id": None,
                    "content": "Claimed task placeholder",
                    "metadata": {},
                    "task_id": task_id,
                }
            )
            return thoughts

    def correlate_knowledge(
        self, source_id: Any, target_id: Any, relationship: str = "related"
    ) -> Any:
        """Create a simple edge between knowledge nodes (stub)."""
        with self.db.get_session() as session:
            return KnowledgeRepository.create_edge(
                session,
                source_id=int(source_id),
                target_id=int(target_id),
                relationship_type=relationship,
            )

import asyncio
from core.knowledge_manager import KnowledgeManager
from core.db_manager import get_db_manager
from loguru import logger

async def test_knowledge_graph():
    logger.info("Starting Knowledge Graph Test...")
    
    km = KnowledgeManager()
    
    # 1. Add an error pattern and solution
    error_msg = "ConnectionTimeout: Failed to connect to gRPC server at localhost:50051"
    solution_msg = "Ensure the IPC Bridge is running by executing 'python core/main.py'"
    
    logger.info("Adding error pattern...")
    error_node = km.add_error_pattern(error_msg, solution_msg, task_id="AAS-207")
    logger.info(f"Created error node: {error_node.id}")
    
    # 2. Search for solutions
    logger.info("Searching for solutions...")
    solutions = km.find_solutions("connection timeout")
    
    for sol in solutions:
        logger.info(f"Found Solution: {sol['content']}")
        
    # 3. Index a task result
    logger.info("Indexing task result...")
    km.index_task_result("AAS-201", True, "Centralized Config Service implemented and verified.")
    
    logger.success("Knowledge Graph Test Completed Successfully!")

if __name__ == "__main__":
    asyncio.run(test_knowledge_graph())

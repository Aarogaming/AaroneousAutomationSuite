"""
ARGO (Agent Runtime & Goal Orchestrator) client for AAS.

This module provides integration with ARGO for autonomous task decomposition,
execution, and memory persistence. ARGO is a Python-based agent runtime
designed for goal-oriented planning and execution.
"""

import json
import asyncio
from pathlib import Path
from typing import List, Dict, Any, Optional
from dataclasses import dataclass
from loguru import logger
import httpx


@dataclass
class Subtask:
    """Represents a decomposed subtask from ARGO."""
    id: str
    title: str
    description: str
    dependencies: List[str]
    estimated_time: str
    has_clear_goal: bool
    tools_required: List[str]


@dataclass
class TaskResult:
    """Result of a task execution."""
    subtask_id: str
    status: str  # "success", "failure", "partial"
    output: str
    artifacts: List[str]
    errors: List[str]
    execution_time: float


class ARGOClient:
    """
    Client for interacting with ARGO agent runtime.
    
    ARGO provides task decomposition, autonomous execution, and memory
    persistence for complex multi-step goals.
    """
    
    def __init__(
        self,
        model_endpoint: str = "http://localhost:11434",
        memory_path: str = "artifacts/argo/memory",
        max_iterations: int = 10,
        tool_registry: Optional[Dict[str, Any]] = None
    ):
        """
        Initialize ARGO client.
        
        Args:
            model_endpoint: Ollama or LocalAI endpoint URL
            memory_path: Directory for persistent memory storage
            max_iterations: Maximum planning iterations
            tool_registry: Dictionary of available tools/functions
        """
        self.model_endpoint = model_endpoint
        self.memory_path = Path(memory_path)
        self.max_iterations = max_iterations
        self.tool_registry = tool_registry or {}
        
        # Ensure memory path exists
        self.memory_path.mkdir(parents=True, exist_ok=True)
        logger.info(f"ARGO client initialized with memory at {self.memory_path}")
    
    async def decompose_task(
        self,
        task: str,
        constraints: Optional[Dict[str, Any]] = None
    ) -> List[Subtask]:
        """
        Decompose a high-level task into subtasks.
        
        Args:
            task: High-level task description
            constraints: Optional constraints (max_subtasks, time_limit, etc.)
        
        Returns:
            List of Subtask objects
        """
        logger.info(f"Decomposing task: {task}")
        constraints = constraints or {}
        
        # Build prompt for task decomposition
        prompt = self._build_decomposition_prompt(task, constraints)
        
        # Query model
        async with httpx.AsyncClient(timeout=60.0) as client:
            try:
                response = await client.post(
                    f"{self.model_endpoint}/api/generate",
                    json={
                        "model": "mistral",
                        "prompt": prompt,
                        "stream": False
                    }
                )
                response.raise_for_status()
                result = response.json()
                
                # Parse response into subtasks
                subtasks = self._parse_subtasks(result["response"])
                
                # Store in memory
                self._save_to_memory("decomposition", {
                    "task": task,
                    "constraints": constraints,
                    "subtasks": [vars(st) for st in subtasks]
                })
                
                logger.info(f"Decomposed into {len(subtasks)} subtasks")
                return subtasks
                
            except httpx.HTTPError as e:
                logger.error(f"Failed to decompose task: {e}")
                raise
    
    async def execute_subtask(self, subtask: Subtask) -> TaskResult:
        """
        Execute a single subtask using available tools.
        
        Args:
            subtask: Subtask to execute
        
        Returns:
            TaskResult with execution details
        """
        logger.info(f"Executing subtask: {subtask.title}")
        start_time = asyncio.get_event_loop().time()
        
        # Build execution prompt
        prompt = self._build_execution_prompt(subtask)
        
        # Execute with model
        async with httpx.AsyncClient(timeout=120.0) as client:
            try:
                response = await client.post(
                    f"{self.model_endpoint}/api/generate",
                    json={
                        "model": "codellama",
                        "prompt": prompt,
                        "stream": False
                    }
                )
                response.raise_for_status()
                result = response.json()
                
                execution_time = asyncio.get_event_loop().time() - start_time
                
                # Parse execution result
                task_result = TaskResult(
                    subtask_id=subtask.id,
                    status="success",
                    output=result["response"],
                    artifacts=[],
                    errors=[],
                    execution_time=execution_time
                )
                
                # Store in memory
                self._save_to_memory("execution", {
                    "subtask_id": subtask.id,
                    "result": vars(task_result)
                })
                
                logger.info(f"Subtask completed in {execution_time:.2f}s")
                return task_result
                
            except httpx.HTTPError as e:
                logger.error(f"Failed to execute subtask: {e}")
                execution_time = asyncio.get_event_loop().time() - start_time
                return TaskResult(
                    subtask_id=subtask.id,
                    status="failure",
                    output="",
                    artifacts=[],
                    errors=[str(e)],
                    execution_time=execution_time
                )
    
    async def execute_goal(
        self,
        goal: str,
        context: Optional[Dict[str, Any]] = None
    ) -> Dict[str, Any]:
        """
        Execute a high-level goal end-to-end.
        
        Args:
            goal: High-level goal description
            context: Optional context information
        
        Returns:
            Dictionary with execution results
        """
        logger.info(f"Executing goal: {goal}")
        
        # Decompose goal into subtasks
        subtasks = await self.decompose_task(goal)
        
        # Execute each subtask
        results = []
        for subtask in subtasks:
            result = await self.execute_subtask(subtask)
            results.append(result)
            
            # Abort if critical failure
            if result.status == "failure" and not subtask.dependencies:
                logger.warning(f"Critical subtask failed: {subtask.title}")
                break
        
        # Synthesize results
        final_result = await self.synthesize_results(results)
        
        return {
            "goal": goal,
            "subtasks": len(subtasks),
            "completed": sum(1 for r in results if r.status == "success"),
            "failed": sum(1 for r in results if r.status == "failure"),
            "output": final_result,
            "results": [vars(r) for r in results]
        }
    
    async def synthesize_results(self, results: List[TaskResult]) -> str:
        """
        Synthesize multiple task results into a coherent summary.
        
        Args:
            results: List of TaskResult objects
        
        Returns:
            Synthesized summary string
        """
        logger.info("Synthesizing results from subtasks")
        
        # Build synthesis prompt
        outputs = "\n\n".join([
            f"Subtask {r.subtask_id}:\n{r.output}"
            for r in results if r.status == "success"
        ])
        
        prompt = f"""Synthesize the following subtask results into a coherent summary:

{outputs}

Provide a comprehensive summary that integrates all completed work."""
        
        async with httpx.AsyncClient(timeout=60.0) as client:
            try:
                response = await client.post(
                    f"{self.model_endpoint}/api/generate",
                    json={
                        "model": "mistral",
                        "prompt": prompt,
                        "stream": False
                    }
                )
                response.raise_for_status()
                result = response.json()
                return result["response"]
            except httpx.HTTPError as e:
                logger.error(f"Failed to synthesize results: {e}")
                return "Failed to synthesize results."
    
    def _build_decomposition_prompt(
        self,
        task: str,
        constraints: Dict[str, Any]
    ) -> str:
        """Build prompt for task decomposition."""
        max_subtasks = constraints.get("max_subtasks", 5)
        time_limit = constraints.get("time_limit", "unlimited")
        
        return f"""You are a task planning agent. Decompose the following task into clear, actionable subtasks.

Task: {task}

Constraints:
- Maximum subtasks: {max_subtasks}
- Time limit: {time_limit}

For each subtask, provide:
1. ID (e.g., ST-001)
2. Title (concise)
3. Description (what needs to be done)
4. Dependencies (IDs of subtasks that must complete first)
5. Estimated time
6. Tools required

Format your response as JSON:
[
  {{
    "id": "ST-001",
    "title": "...",
    "description": "...",
    "dependencies": [],
    "estimated_time": "...",
    "tools_required": [...]
  }}
]
"""
    
    def _build_execution_prompt(self, subtask: Subtask) -> str:
        """Build prompt for subtask execution."""
        return f"""Execute the following subtask:

Title: {subtask.title}
Description: {subtask.description}
Tools available: {', '.join(subtask.tools_required)}

Provide detailed steps and output for completing this subtask."""
    
    def _parse_subtasks(self, response: str) -> List[Subtask]:
        """Parse model response into Subtask objects."""
        try:
            # Extract JSON from response
            start = response.find("[")
            end = response.rfind("]") + 1
            json_str = response[start:end]
            
            data = json.loads(json_str)
            
            subtasks = []
            for item in data:
                subtasks.append(Subtask(
                    id=item.get("id", f"ST-{len(subtasks)+1:03d}"),
                    title=item.get("title", "Untitled"),
                    description=item.get("description", ""),
                    dependencies=item.get("dependencies", []),
                    estimated_time=item.get("estimated_time", "unknown"),
                    has_clear_goal=bool(item.get("description")),
                    tools_required=item.get("tools_required", [])
                ))
            
            return subtasks
        except (json.JSONDecodeError, ValueError) as e:
            logger.warning(f"Failed to parse subtasks JSON: {e}")
            # Fallback: create single subtask
            return [Subtask(
                id="ST-001",
                title="Original Task",
                description=response[:200],
                dependencies=[],
                estimated_time="unknown",
                has_clear_goal=True,
                tools_required=[]
            )]
    
    def _save_to_memory(self, category: str, data: Dict[str, Any]) -> None:
        """Save data to persistent memory."""
        memory_file = self.memory_path / f"{category}.jsonl"
        
        with memory_file.open("a") as f:
            f.write(json.dumps(data) + "\n")
        
        logger.debug(f"Saved to memory: {category}")
    
    def load_memory(self, category: str) -> List[Dict[str, Any]]:
        """
        Load all memory entries for a category.
        
        Args:
            category: Memory category (decomposition, execution, etc.)
        
        Returns:
            List of memory entries
        """
        memory_file = self.memory_path / f"{category}.jsonl"
        
        if not memory_file.exists():
            return []
        
        entries = []
        with memory_file.open("r") as f:
            for line in f:
                try:
                    entries.append(json.loads(line))
                except json.JSONDecodeError:
                    continue
        
        return entries
    
    def clear_memory(self, category: Optional[str] = None) -> None:
        """
        Clear memory entries.
        
        Args:
            category: Specific category to clear, or None for all
        """
        if category:
            memory_file = self.memory_path / f"{category}.jsonl"
            if memory_file.exists():
                memory_file.unlink()
                logger.info(f"Cleared memory: {category}")
        else:
            for file in self.memory_path.glob("*.jsonl"):
                file.unlink()
            logger.info("Cleared all memory")

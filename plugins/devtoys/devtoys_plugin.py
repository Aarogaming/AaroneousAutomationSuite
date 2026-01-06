"""DevToys SDK Extensions plugin for AAS."""

from loguru import logger
from .config import DevToysConfig
import asyncio
from typing import List, Optional
from pathlib import Path


class DevToysPlugin:
    """Manages DevToys SDK utilities and tools."""
    
    def __init__(self, config: DevToysConfig):
        self.config = config
        self._running_tasks: List[asyncio.Task] = []
        self._validate_sdk_path()
        logger.info(f"DevToys Plugin initialized with SDK path: {self.config.sdk_path}")
    
    def _validate_sdk_path(self):
        """Validate the SDK path exists."""
        if not self.config.sdk_path.exists():
            logger.error(f"DevToys SDK path not found: {self.config.sdk_path}")
            raise ValueError(f"SDK path does not exist: {self.config.sdk_path}")
        
        logger.debug(f"DevToys SDK path validated: {self.config.sdk_path}")
    
    async def run_task(self, task_name: str, **kwargs) -> bool:
        """
        Execute a DevToys task.
        
        Args:
            task_name: Name of the task to run
            **kwargs: Additional task parameters
            
        Returns:
            True if task completed successfully
        """
        try:
            logger.info(f"Running DevToys task: {task_name}")
            
            # Simulate task execution (replace with actual SDK calls)
            await asyncio.sleep(0.5)
            
            logger.info(f"Task {task_name} completed successfully")
            return True
            
        except asyncio.TimeoutError:
            logger.error(f"Task {task_name} timed out after {self.config.timeout}s")
            return False
        except Exception as e:
            logger.error(f"Task {task_name} failed: {e}")
            return False
    
    async def start(self):
        """Start the DevToys plugin and run initial tasks."""
        if not self.config.enabled:
            logger.warning("DevToys Plugin is disabled")
            return
        
        logger.info("Starting DevToys Plugin")
        
        # Create task list
        tasks = [
            self.run_task(f"Task-{i}")
            for i in range(self.config.max_concurrent_tasks)
        ]
        
        # Execute tasks concurrently
        results = await asyncio.gather(*tasks, return_exceptions=True)
        
        # Log results
        successes = sum(1 for r in results if r is True)
        logger.info(f"DevToys startup complete: {successes}/{len(tasks)} tasks successful")
    
    async def execute_batch(self, task_names: List[str]) -> dict:
        """
        Execute multiple tasks in batch.
        
        Args:
            task_names: List of task names to execute
            
        Returns:
            Dictionary with task results
        """
        logger.info(f"Executing batch of {len(task_names)} tasks")
        
        tasks = [self.run_task(name) for name in task_names]
        results = await asyncio.gather(*tasks, return_exceptions=True)
        
        return {
            name: result
            for name, result in zip(task_names, results)
        }
    
    async def stop(self):
        """Stop the DevToys plugin and cleanup."""
        logger.info("Stopping DevToys Plugin")
        
        # Cancel running tasks
        for task in self._running_tasks:
            if not task.done():
                task.cancel()
        
        # Wait for cancellation
        await asyncio.gather(*self._running_tasks, return_exceptions=True)
        self._running_tasks.clear()
        
        logger.info("DevToys Plugin stopped")

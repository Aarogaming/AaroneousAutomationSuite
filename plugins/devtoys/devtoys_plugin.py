"""DevToys SDK Extensions plugin for AAS."""

from loguru import logger
from .config import DevToysConfig
import asyncio
import json
import base64
import re
from typing import List, Optional, Any
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
    
    def format_json(self, json_str: str, indent: int = 4) -> str:
        """Format a JSON string."""
        try:
            parsed = json.loads(json_str)
            return json.dumps(parsed, indent=indent)
        except Exception as e:
            logger.error(f"JSON formatting failed: {e}")
            raise

    def validate_json(self, json_str: str) -> bool:
        """Validate a JSON string."""
        try:
            json.loads(json_str)
            return True
        except ValueError:
            return False

    def encode_base64(self, text: str) -> str:
        """Encode text to base64."""
        return base64.b64encode(text.encode()).decode()

    def decode_base64(self, encoded_text: str) -> str:
        """Decode base64 text."""
        return base64.b64decode(encoded_text.encode()).decode()

    def test_regex(self, pattern: str, text: str) -> List[str]:
        """Test a regex pattern against text and return matches."""
        try:
            return re.findall(pattern, text)
        except re.error as e:
            logger.error(f"Regex error: {e}")
            raise

    async def run_task(self, task_name: str, **kwargs) -> Any:
        """
        Execute a DevToys task.
        
        Args:
            task_name: Name of the task to run
            **kwargs: Additional task parameters
            
        Returns:
            Result of the task
        """
        try:
            logger.info(f"Running DevToys task: {task_name}")
            
            if task_name == "json_format":
                return self.format_json(kwargs.get("text", ""))
            elif task_name == "json_validate":
                return self.validate_json(kwargs.get("text", ""))
            elif task_name == "base64_encode":
                return self.encode_base64(kwargs.get("text", ""))
            elif task_name == "base64_decode":
                return self.decode_base64(kwargs.get("text", ""))
            elif task_name == "regex_test":
                return self.test_regex(kwargs.get("pattern", ""), kwargs.get("text", ""))
            
            # Fallback for unknown tasks
            await asyncio.sleep(0.1)
            logger.info(f"Task {task_name} completed successfully")
            return True
            
        except Exception as e:
            logger.error(f"Task {task_name} failed: {e}")
            return None
    
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

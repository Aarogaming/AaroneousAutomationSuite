import asyncio
from typing import Any
from loguru import logger
from core.db_models import TaskPriority


class BackgroundWorker:
    """
    Asynchronous Task Queue with Priority Lanes.
    Handles background execution of tasks without blocking the main loop.
    """

    def __init__(self, task_manager: Any, max_workers: int = 4) -> None:
        self.task_manager = task_manager
        self.max_workers = max_workers
        self.queues: dict[TaskPriority, asyncio.Queue[str]] = {
            priority: asyncio.Queue() for priority in TaskPriority
        }
        self.workers: dict[TaskPriority, list[asyncio.Task[None]]] = {}
        self.is_running = False

    async def start(self) -> None:
        """Start the background workers."""
        if self.is_running:
            return

        self.is_running = True
        for priority in TaskPriority:
            self.workers[priority] = [
                asyncio.create_task(self.process_queue(priority))
                for _ in range(
                    self.max_workers if priority == TaskPriority.URGENT else 2
                )
            ]
        logger.info(f"BackgroundWorker started with {len(self.workers)} priority lanes")

    async def stop(self) -> None:
        """Stop the background workers."""
        self.is_running = False
        for _priority, workers in self.workers.items():
            for worker in workers:
                worker.cancel()
        logger.info("BackgroundWorker stopped")

    async def enqueue(
        self, task_id: str, priority: TaskPriority = TaskPriority.MEDIUM
    ) -> None:
        """Enqueue a task for background processing."""
        await self.queues[priority].put(task_id)
        logger.debug(f"Enqueued task {task_id} with priority {priority}")

    async def process_queue(self, priority: TaskPriority) -> None:
        """Worker loop for a specific priority lane."""
        while self.is_running:
            try:
                task_id = await self.queues[priority].get()
                logger.info(f"Processing task {task_id} in {priority} lane")

                # Execute the task
                await self._execute_task(task_id)

                self.queues[priority].task_done()
            except asyncio.CancelledError:
                break
            except Exception as e:
                logger.error(f"Error in background worker ({priority}): {e}")
                await asyncio.sleep(5)  # Backoff on error

    async def _execute_task(self, task_id: str) -> None:
        """Execute a single task offline."""
        # In a real implementation, this would involve calling the appropriate plugin or tool
        # For now, we'll simulate execution and update the task status
        try:
            # 1. Claim the task if not already claimed
            # (The TaskManager.claim_task handles DB locking)

            # 2. Simulate work
            await asyncio.sleep(2)

            # 3. Mark as completed
            self.task_manager.complete_task(task_id)
            logger.success(f"Background task {task_id} completed successfully")

        except Exception as e:
            logger.error(f"Failed to execute background task {task_id}: {e}")
            # Here we could implement retry logic or mark as failed

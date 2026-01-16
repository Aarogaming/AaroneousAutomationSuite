"""Event dispatcher for Penpot plugin."""

from loguru import logger
from typing import Callable, Dict, List, Any, Optional
import asyncio


class EventDispatcher:
    """Facilitates event-driven communication between components."""

    def __init__(self):
        self.subscribers: Dict[str, List[Callable]] = {}
        logger.debug("EventDispatcher initialized")

    def subscribe(self, event_name: str, callback: Callable):
        """
        Subscribe to an event.

        Args:
            event_name: Name of the event to subscribe to
            callback: Async callback function to invoke on event
        """
        if event_name not in self.subscribers:
            self.subscribers[event_name] = []

        self.subscribers[event_name].append(callback)
        logger.debug(f"Subscriber added for event: {event_name}")

    def unsubscribe(self, event_name: str, callback: Callable):
        """
        Unsubscribe from an event.

        Args:
            event_name: Name of the event
            callback: Callback function to remove
        """
        if event_name in self.subscribers:
            try:
                self.subscribers[event_name].remove(callback)
                logger.debug(f"Subscriber removed from event: {event_name}")
            except ValueError:
                logger.warning(f"Callback not found for event: {event_name}")

    async def dispatch_event(self, event_name: str, payload: Any):
        """
        Dispatch an event to all subscribers.

        Args:
            event_name: Name of the event
            payload: Data to pass to subscribers
        """
        if event_name not in self.subscribers:
            logger.debug(f"No subscribers for event: {event_name}")
            return

        logger.debug(
            f"Dispatching event: {event_name} to {len(self.subscribers[event_name])} subscribers"
        )

        tasks = []
        for callback in self.subscribers[event_name]:
            try:
                # Handle both sync and async callbacks
                if asyncio.iscoroutinefunction(callback):
                    tasks.append(callback(payload))
                else:
                    # Wrap sync callback in async
                    tasks.append(asyncio.to_thread(callback, payload))
            except Exception as e:
                logger.error(f"Error preparing callback for {event_name}: {e}")

        # Execute all callbacks concurrently
        if tasks:
            results = await asyncio.gather(*tasks, return_exceptions=True)

            # Log any exceptions
            for i, result in enumerate(results):
                if isinstance(result, Exception):
                    logger.error(f"Callback {i} for {event_name} raised: {result}")

    def clear_subscribers(self, event_name: Optional[str] = None):
        """
        Clear subscribers for an event or all events.

        Args:
            event_name: Optional event name to clear. If None, clears all.
        """
        if event_name:
            self.subscribers[event_name] = []
            logger.debug(f"Cleared subscribers for event: {event_name}")
        else:
            self.subscribers.clear()
            logger.debug("Cleared all event subscribers")

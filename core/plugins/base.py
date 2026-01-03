"""
Plugin Base - Standardized interface for all AAS plugins.

This module defines the base class that all plugins must inherit from
to ensure consistent lifecycle management and Hub integration.
"""

from abc import ABC, abstractmethod
from typing import Dict, Any, Optional
from loguru import logger
from core.config.manager import AASConfig


class PluginBase(ABC):
    """
    Abstract base class for all AAS plugins.
    
    Plugins are modular extensions that provide specific functionality
    while leveraging the core Hub services (Tasks, DB, Artifacts).
    """
    
    def __init__(self, name: str, config: AASConfig, hub: Any):
        self.name = name
        self.config = config
        self.hub = hub
        logger.info(f"Plugin '{self.name}' initialized")

    @abstractmethod
    async def setup(self) -> bool:
        """
        Perform any necessary setup (e.g., connecting to external APIs).
        
        Returns:
            True if setup was successful, False otherwise.
        """
        pass

    @abstractmethod
    async def shutdown(self) -> bool:
        """
        Perform cleanup during system shutdown.
        
        Returns:
            True if shutdown was successful.
        """
        pass

    def get_info(self) -> Dict[str, Any]:
        """Return metadata about the plugin."""
        return {
            "name": self.name,
            "type": self.__class__.__name__,
            "version": getattr(self, "version", "1.0.0")
        }

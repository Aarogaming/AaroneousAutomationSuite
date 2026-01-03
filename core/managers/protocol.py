"""
Manager Protocol - Standard interface for all AAS managers.

Ensures consistency across the manager ecosystem for status reporting,
validation, and lifecycle management.
"""

from typing import Protocol, Dict, Any, runtime_checkable


@runtime_checkable
class ManagerProtocol(Protocol):
    """Standard interface all AAS managers should implement."""
    
    def get_status(self) -> Dict[str, Any]:
        """
        Return high-level manager status and metrics.
        
        Returns:
            Dict containing type, version, and health metrics.
        """
        ...
    
    def validate(self) -> bool:
        """
        Perform self-validation of configuration and dependencies.
        
        Returns:
            True if valid, False otherwise.
        """
        ...

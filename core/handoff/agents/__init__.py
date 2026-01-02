"""
Local agent framework integration package.

This package provides clients for ARGO agent runtime, enabling task decomposition,
autonomous execution, and memory persistence.
"""

from .argo_client import ARGOClient, Subtask, TaskResult

__all__ = ["ARGOClient", "Subtask", "TaskResult"]

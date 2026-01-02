"""
Workflow automation integration package.

This package provides clients for n8n and Flowise workflow automation platforms.
"""

from .n8n_client import N8NClient, WorkflowExecution, Workflow, get_workflow_template

__all__ = [
    "N8NClient",
    "WorkflowExecution",
    "Workflow",
    "get_workflow_template"
]

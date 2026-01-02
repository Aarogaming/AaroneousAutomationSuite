"""
Knowledge base integration package.

This package provides clients for AnythingLLM and other document-based knowledge systems.
"""

from .anything_llm import (
    AnythingLLMClient,
    QueryResponse,
    Workspace,
    Document,
    get_workspace_template
)

__all__ = [
    "AnythingLLMClient",
    "QueryResponse",
    "Workspace",
    "Document",
    "get_workspace_template"
]

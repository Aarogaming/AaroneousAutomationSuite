"""
AnythingLLM knowledge base client for AAS.

This module provides integration with AnythingLLM for document-based
knowledge retrieval, embeddings, and chat interfaces.
"""

import httpx
from typing import Dict, Any, List, Optional
from dataclasses import dataclass
from pathlib import Path
from loguru import logger


@dataclass
class QueryResponse:
    """Response from AnythingLLM query."""
    text: str
    sources: List[Dict[str, Any]]
    confidence: float
    workspace_id: str


@dataclass
class Workspace:
    """Represents an AnythingLLM workspace."""
    id: str
    name: str
    slug: str
    document_count: int
    chat_mode: str  # "chat" or "query"
    created_at: str


@dataclass
class Document:
    """Represents a document in AnythingLLM."""
    id: str
    name: str
    type: str  # "pdf", "markdown", "txt", etc.
    location: str
    workspace_id: str
    cached: bool


class AnythingLLMClient:
    """
    Client for interacting with AnythingLLM knowledge base.
    
    AnythingLLM provides document embeddings, vector search, and
    chat interfaces with private document collections.
    """
    
    def __init__(
        self,
        base_url: str = "http://localhost:3001",
        api_key: Optional[str] = None
    ):
        """
        Initialize AnythingLLM client.
        
        Args:
            base_url: AnythingLLM server URL
            api_key: Optional API key for authentication
        """
        self.base_url = base_url.rstrip("/")
        self.api_key = api_key
        
        self.headers = {
            "Content-Type": "application/json"
        }
        if api_key:
            self.headers["Authorization"] = f"Bearer {api_key}"
        
        logger.info(f"AnythingLLM client initialized: {self.base_url}")
    
    async def query(
        self,
        workspace_id: str,
        question: str,
        mode: str = "query",
        include_sources: bool = True
    ) -> QueryResponse:
        """
        Query a workspace with a question.
        
        Args:
            workspace_id: Workspace ID or slug
            question: Question to ask
            mode: "query" for direct answer, "chat" for conversational
            include_sources: Whether to include source documents
        
        Returns:
            QueryResponse with answer and sources
        """
        url = f"{self.base_url}/api/workspace/{workspace_id}/chat"
        
        logger.info(f"Querying workspace '{workspace_id}': {question[:50]}...")
        
        payload = {
            "message": question,
            "mode": mode
        }
        
        async with httpx.AsyncClient(timeout=60.0) as client:
            try:
                response = await client.post(
                    url,
                    json=payload,
                    headers=self.headers
                )
                response.raise_for_status()
                
                data = response.json()
                
                # Parse response
                query_response = QueryResponse(
                    text=data.get("textResponse", ""),
                    sources=data.get("sources", []) if include_sources else [],
                    confidence=data.get("confidence", 0.0),
                    workspace_id=workspace_id
                )
                
                logger.info(f"Query completed with {len(query_response.sources)} sources")
                return query_response
                
            except httpx.HTTPError as e:
                logger.error(f"Failed to query workspace: {e}")
                raise
    
    async def create_workspace(
        self,
        name: str,
        documents: Optional[List[str]] = None
    ) -> Workspace:
        """
        Create a new workspace.
        
        Args:
            name: Workspace name
            documents: Optional list of document paths to add
        
        Returns:
            Workspace object
        """
        url = f"{self.base_url}/api/workspace/new"
        
        logger.info(f"Creating workspace: {name}")
        
        payload = {"name": name}
        
        async with httpx.AsyncClient(timeout=30.0) as client:
            try:
                response = await client.post(
                    url,
                    json=payload,
                    headers=self.headers
                )
                response.raise_for_status()
                
                data = response.json()
                workspace_data = data.get("workspace", {})
                
                workspace = Workspace(
                    id=workspace_data.get("id", ""),
                    name=workspace_data.get("name", name),
                    slug=workspace_data.get("slug", name.lower().replace(" ", "-")),
                    document_count=0,
                    chat_mode="query",
                    created_at=workspace_data.get("createdAt", "")
                )
                
                # Add documents if provided
                if documents:
                    for doc_path in documents:
                        await self.upload_document(workspace.id, doc_path)
                
                logger.info(f"Workspace created: {workspace.slug}")
                return workspace
                
            except httpx.HTTPError as e:
                logger.error(f"Failed to create workspace: {e}")
                raise
    
    async def upload_document(
        self,
        workspace_id: str,
        file_path: str
    ) -> Document:
        """
        Upload a document to a workspace.
        
        Args:
            workspace_id: Workspace ID or slug
            file_path: Path to document file
        
        Returns:
            Document object
        """
        url = f"{self.base_url}/api/workspace/{workspace_id}/upload"
        
        file_path_obj = Path(file_path)
        if not file_path_obj.exists():
            raise FileNotFoundError(f"Document not found: {file_path}")
        
        logger.info(f"Uploading document to workspace '{workspace_id}': {file_path_obj.name}")
        
        async with httpx.AsyncClient(timeout=120.0) as client:
            try:
                with file_path_obj.open("rb") as f:
                    files = {"file": (file_path_obj.name, f, "application/octet-stream")}
                    response = await client.post(
                        url,
                        files=files,
                        headers={k: v for k, v in self.headers.items() if k != "Content-Type"}
                    )
                response.raise_for_status()
                
                data = response.json()
                doc_data = data.get("document", {})
                
                document = Document(
                    id=doc_data.get("id", ""),
                    name=doc_data.get("name", file_path_obj.name),
                    type=file_path_obj.suffix.lstrip("."),
                    location=doc_data.get("location", ""),
                    workspace_id=workspace_id,
                    cached=False
                )
                
                logger.info(f"Document uploaded: {document.name}")
                return document
                
            except httpx.HTTPError as e:
                logger.error(f"Failed to upload document: {e}")
                raise
    
    async def get_workspaces(self) -> List[Workspace]:
        """
        Get all workspaces.
        
        Returns:
            List of Workspace objects
        """
        url = f"{self.base_url}/api/workspaces"
        
        logger.info("Fetching workspaces")
        
        async with httpx.AsyncClient(timeout=10.0) as client:
            try:
                response = await client.get(url, headers=self.headers)
                response.raise_for_status()
                
                data = response.json()
                workspaces = []
                
                for ws in data.get("workspaces", []):
                    workspaces.append(Workspace(
                        id=ws.get("id", ""),
                        name=ws.get("name", ""),
                        slug=ws.get("slug", ""),
                        document_count=len(ws.get("documents", [])),
                        chat_mode=ws.get("chatMode", "query"),
                        created_at=ws.get("createdAt", "")
                    ))
                
                logger.info(f"Found {len(workspaces)} workspaces")
                return workspaces
                
            except httpx.HTTPError as e:
                logger.error(f"Failed to fetch workspaces: {e}")
                return []
    
    async def get_workspace(self, workspace_id: str) -> Optional[Workspace]:
        """
        Get a specific workspace.
        
        Args:
            workspace_id: Workspace ID or slug
        
        Returns:
            Workspace object or None
        """
        url = f"{self.base_url}/api/workspace/{workspace_id}"
        
        logger.info(f"Fetching workspace: {workspace_id}")
        
        async with httpx.AsyncClient(timeout=10.0) as client:
            try:
                response = await client.get(url, headers=self.headers)
                response.raise_for_status()
                
                data = response.json()
                ws = data.get("workspace", {})
                
                return Workspace(
                    id=ws.get("id", ""),
                    name=ws.get("name", ""),
                    slug=ws.get("slug", ""),
                    document_count=len(ws.get("documents", [])),
                    chat_mode=ws.get("chatMode", "query"),
                    created_at=ws.get("createdAt", "")
                )
                
            except httpx.HTTPError as e:
                logger.error(f"Failed to fetch workspace: {e}")
                return None
    
    async def delete_workspace(self, workspace_id: str) -> bool:
        """
        Delete a workspace.
        
        Args:
            workspace_id: Workspace ID or slug
        
        Returns:
            True if successful
        """
        url = f"{self.base_url}/api/workspace/{workspace_id}"
        
        logger.info(f"Deleting workspace: {workspace_id}")
        
        async with httpx.AsyncClient(timeout=10.0) as client:
            try:
                response = await client.delete(url, headers=self.headers)
                response.raise_for_status()
                logger.info(f"Workspace deleted: {workspace_id}")
                return True
            except httpx.HTTPError as e:
                logger.error(f"Failed to delete workspace: {e}")
                return False
    
    async def health_check(self) -> bool:
        """
        Check if AnythingLLM server is healthy.
        
        Returns:
            True if server is reachable
        """
        url = f"{self.base_url}/api/system/health"
        
        async with httpx.AsyncClient(timeout=5.0) as client:
            try:
                response = await client.get(url, headers=self.headers)
                return response.status_code == 200
            except httpx.HTTPError:
                return False


# Workspace templates for common use cases
WORKSPACE_TEMPLATES = {
    "wizard101_research": {
        "name": "Wizard101 Combat Research",
        "documents": [
            "docs/COMBAT_MECHANICS.md",
            "core/deimos/src/combat_new.py",
            "artifacts/research/spell_analysis.pdf"
        ],
        "description": "Knowledge base for Wizard101 combat mechanics and spell optimization"
    },
    "aas_documentation": {
        "name": "AAS Project Documentation",
        "documents": [
            "README.md",
            "ROADMAP.md",
            "docs/LOCAL_AGENTS.md",
            ".github/copilot-instructions.md"
        ],
        "description": "Central knowledge base for AAS project documentation"
    },
    "plugin_development": {
        "name": "Plugin Development Guide",
        "documents": [
            "plugins/ai_assistant/assistant.py",
            "plugins/home_assistant/connector.py",
            "plugins/dev_studio/studio.py"
        ],
        "description": "Reference for AAS plugin development patterns"
    }
}


def get_workspace_template(template_name: str) -> Optional[Dict[str, Any]]:
    """
    Get a workspace template by name.
    
    Args:
        template_name: Name of template
    
    Returns:
        Template dictionary or None
    """
    return WORKSPACE_TEMPLATES.get(template_name)

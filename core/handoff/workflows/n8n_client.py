"""
n8n workflow automation client for AAS.

This module provides integration with n8n for visual workflow automation,
enabling automated task pipelines triggered by events or webhooks.
"""

import httpx
from typing import Dict, Any, List, Optional
from dataclasses import dataclass
from loguru import logger


@dataclass
class WorkflowExecution:
    """Represents an n8n workflow execution."""
    execution_id: str
    workflow_id: str
    status: str  # "running", "success", "error"
    started_at: str
    finished_at: Optional[str]
    data: Dict[str, Any]


@dataclass
class Workflow:
    """Represents an n8n workflow."""
    id: str
    name: str
    active: bool
    nodes: int
    connections: int
    tags: List[str]


class N8NClient:
    """
    Client for interacting with n8n workflow automation platform.
    
    n8n provides visual workflow building with 300+ integrations,
    webhook triggers, and scheduled executions.
    """
    
    def __init__(
        self,
        base_url: str = "http://localhost:5678",
        api_key: Optional[str] = None
    ):
        """
        Initialize n8n client.
        
        Args:
            base_url: n8n server URL
            api_key: API key for authentication (if enabled)
        """
        self.base_url = base_url.rstrip("/")
        self.api_key = api_key
        
        self.headers = {}
        if api_key:
            self.headers["X-N8N-API-KEY"] = api_key
        
        logger.info(f"n8n client initialized: {self.base_url}")
    
    async def trigger_workflow(
        self,
        webhook_id: str,
        payload: Dict[str, Any],
        test_mode: bool = False
    ) -> WorkflowExecution:
        """
        Trigger a workflow via webhook.
        
        Args:
            webhook_id: Webhook identifier from n8n workflow
            payload: Data to send to workflow
            test_mode: Whether to run in test mode
        
        Returns:
            WorkflowExecution object
        """
        url = f"{self.base_url}/webhook{'test' if test_mode else ''}/{webhook_id}"
        
        logger.info(f"Triggering n8n workflow: {webhook_id}")
        
        async with httpx.AsyncClient(timeout=30.0) as client:
            try:
                response = await client.post(
                    url,
                    json=payload,
                    headers=self.headers
                )
                response.raise_for_status()
                
                data = response.json()
                
                # n8n webhook responses vary, adapt as needed
                execution = WorkflowExecution(
                    execution_id=data.get("executionId", "unknown"),
                    workflow_id=webhook_id,
                    status="success" if response.status_code == 200 else "error",
                    started_at=data.get("startedAt", ""),
                    finished_at=data.get("finishedAt"),
                    data=data
                )
                
                logger.info(f"Workflow triggered: {execution.execution_id}")
                return execution
                
            except httpx.HTTPError as e:
                logger.error(f"Failed to trigger workflow: {e}")
                raise
    
    async def get_workflows(self) -> List[Workflow]:
        """
        Get all workflows from n8n.
        
        Returns:
            List of Workflow objects
        """
        url = f"{self.base_url}/api/v1/workflows"
        
        logger.info("Fetching workflows from n8n")
        
        async with httpx.AsyncClient(timeout=10.0) as client:
            try:
                response = await client.get(url, headers=self.headers)
                response.raise_for_status()
                
                data = response.json()
                workflows = []
                
                for wf in data.get("data", []):
                    workflows.append(Workflow(
                        id=wf["id"],
                        name=wf["name"],
                        active=wf.get("active", False),
                        nodes=len(wf.get("nodes", [])),
                        connections=len(wf.get("connections", {})),
                        tags=wf.get("tags", [])
                    ))
                
                logger.info(f"Found {len(workflows)} workflows")
                return workflows
                
            except httpx.HTTPError as e:
                logger.error(f"Failed to fetch workflows: {e}")
                return []
    
    async def get_execution(self, execution_id: str) -> Optional[WorkflowExecution]:
        """
        Get details of a specific workflow execution.
        
        Args:
            execution_id: Execution ID from n8n
        
        Returns:
            WorkflowExecution object or None
        """
        url = f"{self.base_url}/api/v1/executions/{execution_id}"
        
        logger.info(f"Fetching execution: {execution_id}")
        
        async with httpx.AsyncClient(timeout=10.0) as client:
            try:
                response = await client.get(url, headers=self.headers)
                response.raise_for_status()
                
                data = response.json()
                
                return WorkflowExecution(
                    execution_id=data["id"],
                    workflow_id=data.get("workflowId", "unknown"),
                    status=data.get("finished") and "success" or "running",
                    started_at=data.get("startedAt", ""),
                    finished_at=data.get("stoppedAt"),
                    data=data.get("data", {})
                )
                
            except httpx.HTTPError as e:
                logger.error(f"Failed to fetch execution: {e}")
                return None
    
    async def activate_workflow(self, workflow_id: str) -> bool:
        """
        Activate a workflow.
        
        Args:
            workflow_id: Workflow ID to activate
        
        Returns:
            True if successful
        """
        url = f"{self.base_url}/api/v1/workflows/{workflow_id}/activate"
        
        logger.info(f"Activating workflow: {workflow_id}")
        
        async with httpx.AsyncClient(timeout=10.0) as client:
            try:
                response = await client.post(url, headers=self.headers)
                response.raise_for_status()
                logger.info(f"Workflow activated: {workflow_id}")
                return True
            except httpx.HTTPError as e:
                logger.error(f"Failed to activate workflow: {e}")
                return False
    
    async def deactivate_workflow(self, workflow_id: str) -> bool:
        """
        Deactivate a workflow.
        
        Args:
            workflow_id: Workflow ID to deactivate
        
        Returns:
            True if successful
        """
        url = f"{self.base_url}/api/v1/workflows/{workflow_id}/deactivate"
        
        logger.info(f"Deactivating workflow: {workflow_id}")
        
        async with httpx.AsyncClient(timeout=10.0) as client:
            try:
                response = await client.post(url, headers=self.headers)
                response.raise_for_status()
                logger.info(f"Workflow deactivated: {workflow_id}")
                return True
            except httpx.HTTPError as e:
                logger.error(f"Failed to deactivate workflow: {e}")
                return False
    
    async def health_check(self) -> bool:
        """
        Check if n8n server is healthy.
        
        Returns:
            True if server is reachable
        """
        url = f"{self.base_url}/healthz"
        
        async with httpx.AsyncClient(timeout=5.0) as client:
            try:
                response = await client.get(url)
                return response.status_code == 200
            except httpx.HTTPError:
                return False


# Workflow template library
WORKFLOW_TEMPLATES = {
    "combat_analysis": {
        "name": "Combat Log Analysis",
        "description": "Analyze combat logs, send to Ollama, create Linear issues",
        "webhook_id": "combat-analysis-v2",
        "required_payload": ["log_path", "analysis_type"],
        "optional_payload": ["notify_linear"]
    },
    "code_quality_check": {
        "name": "Code Quality Check",
        "description": "Run code quality checks and report issues",
        "webhook_id": "code-quality-check",
        "required_payload": ["code"],
        "optional_payload": ["language", "rules"]
    },
    "task_decomposition": {
        "name": "Task Decomposition",
        "description": "Decompose high-level task into subtasks",
        "webhook_id": "task-decomposition",
        "required_payload": ["task_description"],
        "optional_payload": ["max_subtasks", "priority"]
    }
}


def get_workflow_template(template_name: str) -> Optional[Dict[str, Any]]:
    """
    Get a workflow template by name.
    
    Args:
        template_name: Name of template
    
    Returns:
        Template dictionary or None
    """
    return WORKFLOW_TEMPLATES.get(template_name)

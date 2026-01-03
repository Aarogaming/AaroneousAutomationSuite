import requests
from typing import Optional, Any
from pydantic import SecretStr
from loguru import logger

class LinearSync:
    """
    Linear API Integration for Autonomous Governance.
    Uses the acolegrove96-codex@yahoo.com identity.
    """
    def __init__(self, api_key: SecretStr):
        self.api_key = api_key
        self.url = "https://api.linear.app/graphql"
        self.headers = {
            "Authorization": api_key.get_secret_value(),
            "Content-Type": "application/json",
        }

    def get_active_tasks(self, team_id: str) -> list[dict[str, Any]]:
        """
        Fetches tasks assigned to the AI identity in the 'In Progress' or 'To Do' columns.
        """
        query = """
        query Tasks($teamId: String!) {
          team(id: $teamId) {
            issues(filter: { assignee: { email: { eq: "acolegrove96-codex@yahoo.com" } } }) {
              nodes {
                id
                title
                description
                status { name }
              }
            }
          }
        }
        """
        try:
            response = requests.post(self.url, headers=self.headers, json={'query': query, 'variables': {'teamId': team_id}})
            response.raise_for_status()
            return response.json().get("data", {}).get("team", {}).get("issues", {}).get("nodes", [])
        except Exception as e:
            logger.error(f"LinearSync: Failed to fetch tasks: {e}")
            return []

    def update_task_status(self, issue_id: str, status_id: str):
        """
        Moves a task to a new column (e.g., 'Done').
        """
        mutation = """
        mutation IssueUpdate($id: String!, $statusId: String!) {
          issueUpdate(id: $id, input: { boardOrder: 0, stateId: $statusId }) {
            success
          }
        }
        """
        try:
            response = requests.post(self.url, headers=self.headers, json={'query': mutation, 'variables': {'id': issue_id, 'statusId': status_id}})
            response.raise_for_status()
            logger.success(f"LinearSync: Updated task {issue_id} to status {status_id}")
        except Exception as e:
            logger.error(f"LinearSync: Failed to update task: {e}")

    def create_issue(self, team_id: str, title: str, description: str) -> Optional[str]:
        """
        Creates a new issue in Linear.
        """
        mutation = """
        mutation IssueCreate($teamId: String!, $title: String!, $description: String!) {
          issueCreate(input: { teamId: $teamId, title: $title, description: $description }) {
            success
            issue {
              id
            }
          }
        }
        """
        try:
            response = requests.post(self.url, headers=self.headers, json={
                'query': mutation, 
                'variables': {
                    'teamId': team_id,
                    'title': title,
                    'description': description
                }
            })
            response.raise_for_status()
            data = response.json().get("data", {}).get("issueCreate", {})
            if data.get("success"):
                issue_id = data.get("issue", {}).get("id")
                logger.success(f"LinearSync: Created issue {issue_id}")
                return issue_id
            return None
        except Exception as e:
            logger.error(f"LinearSync: Failed to create issue: {e}")
            return None

    def add_comment(self, issue_id: str, body: str) -> bool:
        """
        Adds a comment to a Linear issue.
        """
        mutation = """
        mutation CommentCreate($issueId: String!, $body: String!) {
          commentCreate(input: { issueId: $issueId, body: $body }) {
            success
          }
        }
        """
        try:
            response = requests.post(self.url, headers=self.headers, json={
                'query': mutation,
                'variables': {'issueId': issue_id, 'body': body}
            })
            response.raise_for_status()
            data = response.json().get("data", {}).get("commentCreate", {})
            if data.get("success"):
                logger.success(f"LinearSync: Added comment to issue {issue_id}")
                return True
            return False
        except Exception as e:
            logger.error(f"LinearSync: Failed to add comment to {issue_id}: {e}")
            return False

    def get_workflow_states(self, team_id: str) -> dict[str, str]:
        """
        Gets workflow states for a team. Returns dict mapping state name -> state ID.
        """
        query = """
        query TeamStates($teamId: String!) {
          team(id: $teamId) {
            states {
              nodes {
                id
                name
              }
            }
          }
        }
        """
        try:
            response = requests.post(self.url, headers=self.headers, json={
                'query': query,
                'variables': {'teamId': team_id}
            })
            response.raise_for_status()
            states = response.json().get("data", {}).get("team", {}).get("states", {}).get("nodes", [])
            state_map = {state["name"]: state["id"] for state in states}
            logger.debug(f"LinearSync: Found {len(state_map)} workflow states")
            return state_map
        except Exception as e:
            logger.error(f"LinearSync: Failed to get workflow states: {e}")
            return {}

    def get_issue_by_identifier(self, team_id: str, task_id: str) -> Optional[str]:
        """
        Gets Linear issue ID from task identifier (e.g., 'AAS-109').
        Uses simple team query and searches client-side.
        """
        query = """
        query TeamIssues($teamId: String!) {
          team(id: $teamId) {
            issues(first: 250) {
              nodes {
                id
                identifier
              }
            }
          }
        }
        """
        try:
            response = requests.post(self.url, headers=self.headers, json={
                'query': query,
                'variables': {'teamId': team_id}
            })
            response.raise_for_status()
            
            data = response.json()
            if "errors" in data:
                logger.error(f"LinearSync: GraphQL errors: {data['errors']}")
                return None
                
            issues = data.get("data", {}).get("team", {}).get("issues", {}).get("nodes", [])
            
            # Search for matching identifier
            for issue in issues:
                if issue.get("identifier") == task_id:
                    logger.debug(f"LinearSync: Found issue {issue['id']} for {task_id}")
                    return issue["id"]
            
            logger.warning(f"LinearSync: No issue found with identifier {task_id} (searched {len(issues)} issues)")
            return None
        except Exception as e:
            logger.error(f"LinearSync: Failed to get issue by identifier {task_id}: {e}")
            return None

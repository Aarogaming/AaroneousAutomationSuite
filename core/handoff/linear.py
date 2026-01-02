import requests
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
            "Authorization": token.get_secret_value() if hasattr(self, 'token') else api_key.get_secret_value(),
            "Content-Type": "application/json",
        }

    def get_active_tasks(self, team_id: str) -> list:
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

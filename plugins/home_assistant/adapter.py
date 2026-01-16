import requests
from typing import Optional, Any, Dict
from loguru import logger
from core.config import AASConfig


class HomeMerlinClient:
    """
    Home Merlin Integration for AAS.
    Allows the suite to interact with smart home devices and sensors.
    """

    def __init__(self, config: AASConfig):
        self.config = config
        self.url = config.home_assistant_url
        self.token = config.home_assistant_token

        if not self.url or not self.token:
            logger.warning(
                "Home Merlin configuration incomplete. Plugin will be disabled."
            )
            self.headers = {}
        else:
            self.headers = {
                "Authorization": f"Bearer {self.token.get_secret_value()}",
                "Content-Type": "application/json",
            }

    def get_state(self, entity_id: str) -> Optional[Dict[str, Any]]:
        """Fetches the state of a specific entity."""
        if not self.headers:
            return None

        endpoint = f"{self.url}/api/states/{entity_id}"
        try:
            response = requests.get(endpoint, headers=self.headers)
            response.raise_for_status()
            return response.json()
        except Exception as e:
            logger.error(f"HomeMerlin: Failed to get state for {entity_id}: {e}")
            return None

    def call_service(
        self, domain: str, service: str, service_data: Dict[str, Any]
    ) -> bool:
        """Calls a service in Home Merlin."""
        if not self.headers:
            return False

        endpoint = f"{self.url}/api/services/{domain}/{service}"
        try:
            response = requests.post(endpoint, headers=self.headers, json=service_data)
            response.raise_for_status()
            logger.success(f"HomeMerlin: Called service {domain}.{service}")
            return True
        except Exception as e:
            logger.error(f"HomeMerlin: Failed to call service {domain}.{service}: {e}")
            return False

    def check_health(self) -> bool:
        """Checks if the Home Merlin API is reachable."""
        if not self.headers:
            return False

        endpoint = f"{self.url}/api/"
        try:
            response = requests.get(endpoint, headers=self.headers)
            response.raise_for_status()
            return response.json().get("message") == "API running."
        except Exception:
            return False

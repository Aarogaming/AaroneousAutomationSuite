import requests
from pydantic import SecretStr
from loguru import logger

class HomeAssistantConnector:
    """
    Home Assistant API Plugin.
    Allows AAS to control smart home devices.
    """
    def __init__(self, base_url: str, token: SecretStr):
        self.base_url = base_url.rstrip("/")
        self.headers = {
            "Authorization": f"Bearer {token.get_secret_value()}",
            "Content-Type": "application/json",
        }

    def get_state(self, entity_id: str) -> dict:
        """
        Fetches the state of a specific entity.
        """
        try:
            url = f"{self.base_url}/api/states/{entity_id}"
            response = requests.get(url, headers=self.headers)
            response.raise_for_status()
            return response.json()
        except Exception as e:
            logger.error(f"HomeAssistant: Failed to get state for {entity_id}: {e}")
            return {}

    def call_service(self, domain: str, service: str, service_data: dict):
        """
        Calls a Home Assistant service (e.g., light.turn_on).
        """
        try:
            url = f"{self.base_url}/api/services/{domain}/{service}"
            response = requests.post(url, headers=self.headers, json=service_data)
            response.raise_for_status()
            logger.success(f"HomeAssistant: Called {domain}.{service}")
            return response.json()
        except Exception as e:
            logger.error(f"HomeAssistant: Failed to call service {domain}.{service}: {e}")
            return None

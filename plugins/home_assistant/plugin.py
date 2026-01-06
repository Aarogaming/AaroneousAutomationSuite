from typing import Optional, Any, Dict
from loguru import logger
from core.config import AASConfig
from core.handoff.home_assistant import HomeAssistantClient

class HomeAssistantPlugin:
    """
    AAS Plugin for Home Assistant.
    Exposes smart home capabilities to the AAS Hub.
    """
    def __init__(self, config: AASConfig):
        self.config = config
        self.client = HomeAssistantClient(config)
        self.enabled = self.client.check_health()
        
        if self.enabled:
            logger.info("Home Assistant Plugin initialized and connected.")
        else:
            logger.warning("Home Assistant Plugin initialized but could not connect to API.")

    def get_entity_status(self, entity_id: str) -> str:
        """Returns a human-readable status of an entity."""
        state = self.client.get_state(entity_id)
        if not state:
            return "Unknown"
        
        friendly_name = state.get("attributes", {}).get("friendly_name", entity_id)
        status = state.get("state", "unknown")
        unit = state.get("attributes", {}).get("unit_of_measurement", "")
        
        return f"{friendly_name} is {status}{unit}"

    def toggle_device(self, entity_id: str) -> bool:
        """Toggles a switch or light."""
        domain = entity_id.split(".")[0]
        return self.client.call_service(domain, "toggle", {"entity_id": entity_id})

    def run_automation(self, automation_id: str) -> bool:
        """Triggers a Home Assistant automation."""
        return self.client.call_service("automation", "trigger", {"entity_id": f"automation.{automation_id}"})

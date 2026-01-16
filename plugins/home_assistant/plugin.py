from loguru import logger
from core.config import AASConfig
from core.guild.home_assistant import HomeMerlinClient


class HomeMerlinPlugin:
    """
    AAS Plugin for Home Merlin.
    Exposes smart home capabilities to the AAS Hub.
    """

    def __init__(self, config: AASConfig):
        self.config = config
        self.client = HomeMerlinClient(config)
        self.enabled = self.client.check_health()

        if self.enabled:
            logger.info("Home Merlin Plugin initialized and connected.")
        else:
            logger.warning(
                "Home Merlin Plugin initialized but could not connect to API."
            )

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
        """Triggers a Home Merlin automation."""
        return self.client.call_service(
            "automation", "trigger", {"entity_id": f"automation.{automation_id}"}
        )
